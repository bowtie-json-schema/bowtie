==================================
Tutorial: Adding An Implementation
==================================

The purpose of `Bowtie` is to support passing :term:`instances <instance>` and :term:`schemas <schema>` through a large number of JSON Schema implementations, collecting their output for comparison.

If you've written or used an implementation of JSON Schema which isn't already supported, let's see how you can add support for it to Bowtie.

Bowtie orchestrates running a number of containers, passing JSON Schema test cases to each one of them, and then collecting and comparing results across implementations.
Any JSON Schema implementation will have some way of getting schemas and instances "into" it for processing.
We'll wrap this implementation-specific API inside a small harness which accepts input from Bowtie over standard input and writes results to standard output in the format Bowtie expects.

As a last step before we get into details, let's summarize some terminology (which you can also skip and refer back to if needed):

.. glossary::

    implementation
        a library or program which implements the JSON Schema specification

    validation API
        the specific function(s), method(s), or similar constructs within the `implementation` which cause it to evaluate a schema against a specific instance

    host language
        the programming language which a particular `implementation` is written in

    test harness
    test runner
        a small program which accepts `test cases <test case>` sent from Bowtie, passes them through a specific `implementation's <implementation>` :term:`validation API`, and writes the results of this validation process out for Bowtie to read

    harness language
        the programming language which the `test harness` itself is written in.
        Typically this will match the `host language`, since doing so will make it easier to call out directly to the `implementation`.

    test case
        a specific JSON schema and instance which Bowtie will pass to any `implementations <implementation>` it is testing

    IHOP
        the *i*\ nput → *h*\ arness → *o*\ utput *p*\ rotocol.
        A JSON protocol governing the structure and semantics of messages which Bowtie will send to `test harnesses <test harness>` as well as the structure and semantics it expects from JSON responses sent back.

.. spelling:word-list::

    nput
    arness
    utput
    rotocol


Prerequisites
-------------

* Bowtie itself, already installed on your machine
* A target `implementation`, which you do *not* necessarily need installed on your machine
* `docker <https://www.docker.com/>`_, `podman <https://podman.io/>`_ or a similarly compatible tool for building OCI container images and running OCI containers


Step 0: Familiarization With the Implementation
-----------------------------------------------

Once you've installed the prerequisites, your first step is to ensure you're familiar with the implementation you're about to add support for, as well as with its `host language`.
If you're its author, you're certainly well qualified :) -- if not, you'll see a few things below which you'll need to find in its API documentation, such as what function(s) or object(s) you use to validate instances under schemas.
If you're not, there shouldn't be a need to be an expert neither in the language nor implementation, as we'll be writing only a small wrapper program, but you definitely will need to know how to compile or run programs in the host language, how to read and write JSON from it, and how to package programs into container images.

For the purposes of this tutorial, we'll write support for a :github:`Lua implementation of JSON Schema <api7/jsonschema>` (one which calls itself simply ``jsonschema`` within the Lua ecosystem, as many implementations tend to).
Bowtie of course already supports this implementation officially, so if you want to see the final result either now or at the end of this tutorial, it's :gh:`here <tree/main/implementations/lua-jsonschema>`.
If you're not already familiar with Lua as a programming language, the below won't serve as a full tutorial of course, but you still should be able to follow along; it's a fairly simple one.

Let's get a Hello World container running which we'll turn into our test harness.

Create a directory somewhere, and within it create a ``Dockerfile`` with these contents:

.. code:: dockerfile

    FROM alpine:3.16
    RUN apk add --no-cache luajit luajit-dev pcre-dev gcc libc-dev curl make cmake && \
        wget 'https://luarocks.org/releases/luarocks-3.9.1.tar.gz' && \
        tar -xf luarocks-3.9.1.tar.gz && cd luarocks-3.9.1 && \
        ./configure && make && make install
    RUN sed -i '/WGET/d' /usr/local/share/lua/5.1/luarocks/fs/tools.lua
    RUN luarocks install jsonschema
    ADD https://raw.githubusercontent.com/rxi/json.lua/master/json.lua .
    COPY bowtie_jsonschema.lua .
    CMD ["luajit", "bowtie_jsonschema.lua"]

Most of the above is slightly *more* complicated than one you'll need to write for your own language, and has to do with some Lua packaging issues that are uninteresting to discuss in detail.
The notable bit is we'll create a ``bowtie_jsonschema.lua`` file, our test harness, and then this container image will invoke it.
Bowtie will then speak to the running harness container.

Let's check everything works.
Create a file named ``bowtie_jsonschema.lua`` with these contents:

.. code:: lua

    print('Hello world')

and build the image (below using ``podman`` but if you're using ``docker``, just substitute it for ``podman`` in all commands below):

.. code:: sh

    podman build --quiet -f Dockerfile -t bowtie-lua-jsonschema

If everything went well, running:

.. code:: sh

    podman run --rm bowtie-lua-jsonschema

should get you some output:

    Hello world

We're off to the races.


Step 1: :term:`IHOP` Here We Come
---------------------------------

From here on out we'll continue to modify the ``bowtie_jsonschema.lua`` file we created above, so keep that file open and make changes to it as directed below.

Bowtie sends JSON requests (or commands) to `test harness` containers over standard input, and expects responses to be sent over standard output.

Each request has a ``cmd`` property which specifies which type of request it is.
Additional properties are arguments to the request.

There are 4 commands every harness must know how to respond to, shown here as a brief excerpt from the full schema specifying the protocol:

.. literalinclude:: ../bowtie/schemas/io-schema.json
    :language: json
    :start-at: oneOf
    :end-at: ]
    :dedent:


Bowtie will send a ``start`` request when first starting a harness, and then at the end will send a ``stop`` request telling the harness to shut down.

Let's start filling out a real test harness implementation by at least reacting to ``start`` and ``stop`` requests.

.. note::

    From here on out in this document it's assumed you rebuild your container image each time you modify the harness via

    .. code:: sh

        podman build -f Dockerfile -t localhost/tutorial-lua-jsonschema

Change your harness to contain:

.. code:: lua

    local json = require 'json'

    local cmds = {
      start = function(_)
        io.stderr:write("STARTING")
        return {}
      end,

      stop = function(_)
        io.stderr:write("STOPPING")
        return {}
      end,
    }

    for line in io.lines() do
      local request = json.decode(line)
      local response = cmds[request.cmd](request)
      io.write(json.encode(response) .. '\n')
    end

If this is your first time reading Lua code, what we've done is create a dispatch table (a mapping from string command names to functions handling each one), and implemented stub functions which simply write to ``stderr`` when called, and then return empty responses.
Any other command other than ``start`` or ``stop`` will blow up, but we're reading and writing JSON!

.. program:: bowtie run

Let's see what happens if we use this nonetheless.
We can pass a hand-crafted `test case` to Bowtie by running:

.. code:: sh

    bowtie run -i localhost/tutorial-lua-jsonschema <<EOF
        {"description": "test case 1", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
        {"description": "test case 2", "schema": {"const": 37}, "tests": [{"description": "not 37", "instance": {}}, {"description": "is 37", "instance": 37}] }
    EOF

which if you now run should produce something like::

    2022-10-05 15:39.59 [info     ] Will speak dialect             dialect=https://json-schema.org/draft/2020-12/schema
    Traceback (most recent call last):
        ...
    TypeError: bowtie._commands.Started() argument after ** must be a mapping, not list

... a nice big inscrutable error message.
Our harness isn't returning valid responses, and Bowtie doesn't know how to handle what we've sent it.
The structure of the protocol we're trying to implement lives in a JSON Schema though, and Bowtie can be told to validate requests and responses using the schema.
You can enable this validation by passing :program:`bowtie run` the :option:`-V` option, which will produce nicer messages while we develop the harness:

.. code:: sh

    bowtie run -i localhost/tutorial-lua-jsonschema -V <<EOF
    {"description": "test case 1", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }
    {"description": "test case 2", "schema": {"const": 37}, "tests": [{"description": "not 37", "instance": {}}, {"description": "is 37", "instance": 37}] }
    EOF
    2022-10-05 20:59.41 [info     ] Will speak dialect             dialect=https://json-schema.org/draft/2020-12/schema
    2022-10-05 20:59.41 [error    ] Invalid response               [localhost/tutorial-lua-jsonschema] errors=[<ValidationError: "[] is not of type 'object'">] request=Start(version=1)
    2022-10-05 20:59.45 [warning  ] Unsupported dialect, skipping implementation. [localhost/tutorial-lua-jsonschema] dialect=https://json-schema.org/draft/2020-12/schema
    {"implementations": {}}
    {"case": {"description": "test case 1", "schema": {}, "tests": [{"description": "a test", "instance": {}, "valid": null}], "comment": null, "registry": null}, "seq": 1}
    {"case": {"description": "test case 2", "schema": {"const": 37}, "tests": [{"description": "not 37", "instance": {}, "valid": null}, {"description": "is 37", "instance": 37, "valid": null}], "comment": null, "registry": null}, "seq": 2}
    2022-10-05 20:59.45 [info     ] Finished                       count=2

which is telling us we're returning JSON arrays to Bowtie instead of JSON objects.
Lua the language has only one container type (``table``), and we've returned ``{}`` which the JSON library guesses means "empty array".
Don't think too hard about Lua's peculiarities, let's just fix it by having a look at what parameters the ``start`` command sends a harness and what it expects back.
The schema says:

.. literalinclude:: ../bowtie/schemas/io-schema.json
    :language: json
    :start-at: "start"
    :end-before: "$defs"
    :dedent:

so ``start`` requests will have two parameters:

    * ``cmd`` which indicates the kind of request being sent (and is present in all requests sent by Bowtie)
    * ``version`` which represents the version of the Bowtie protocol being spoken.
      Today, that version is always ``1``, but that may change in the future, in which case a harness should bail out as it may not understand the requests being sent.

The harness is expected to respond with:

.. literalinclude:: ../bowtie/schemas/io-schema.json
    :language: json
    :start-at: "response"
    :end-before: "dialect"
    :dedent:

which is some metadata about the implementation being tested, and includes things like:

    * its name
    * a URL for its bug tracker for use if issues are found
    * the versions of JSON Schema it supports, identified via URIs

You can also have a look at the full schema for details on the ``stop`` command, but it essentially doesn't require a response, and simply signals the harness that it should exit.

Let's implement both requests.
Change your harness to contain:

.. code:: lua

    local json = require 'json'

    STARTED = false

    local cmds = {
      start = function(request)
        assert(request.version == 1, 'Wrong version!')
        STARTED = true
        return {
          ready = true,
          version = 1,
          implementation = {
            language = 'lua',
            name = 'jsonschema',
            homepage = 'https://github.com/api7/jsonschema',
            issues = 'https://github.com/api7/jsonschema/issues',

            dialects = {
              'http://json-schema.org/draft-07/schema#',
              'http://json-schema.org/draft-06/schema#',
              'http://json-schema.org/draft-04/schema#',
            },
          },
        }
      end,

      stop = function(_)
        assert(STARTED, 'Not started!')
        os.exit(0)
      end,
    }

    for line in io.lines() do
      local request = json.decode(line)
      local response = cmds[request.cmd](request)
      io.write(json.encode(response) .. '\n')
    end

We now return some detail about the implementation when responding to ``start`` requests (sent as JSON), including which versions of the specification it supports.

When stopping, we simply exit successfully.

If you re-run ``bowtie``, you'll see now that it doesn't crash, though it outputs::

    2022-10-11 13:44.40 [info     ] Will speak dialect             dialect=https://json-schema.org/draft/2020-12/schema
    2022-10-11 13:44.40 [warning  ] Unsupported dialect, skipping implementation. [localhost/tutorial-lua-jsonschema] dialect=https://json-schema.org/draft/2020-12/schema
    {"implementations": {}}

Our harness is now properly starting and stopping, but this Lua implementation only supports versions of JSON Schema earlier than Draft 7, and Bowtie is defaulting to a newer version.
Tell Bowtie we are speaking an earlier version by passing the :option:`--dialect` option, i.e. ``bowtie run --dialect 7 -i localhost/tutorial-lua-jsonschema``.

.. tip::

    Any of ``7``, ``draft7``, or the full draft 7 meta schema URI will work to set the dialect in use.


Addendum: Submitting Upstream
-----------------------------

If the implementation you've added isn't already supported by Bowtie, contributing it is very welcome!

Please feel free to :gh:`open an issue <issues/new>` or :gh:`pull request <compare>` adding it to the :gh:`implementations directory <tree/main/implementations>`.

If you do so there are a few additional things to do beyond the above:

* Commit your harness to the ``implementations`` directory in the root of Bowtie's repository, alongside the existing ones.
  Name your harness directory :file:`<{host-language}>-<{implementation-name}>/`.
  Use ASCII-compatible names, so if your implementation is written in C++ and is called ``flooblekins`` within the C++ ecosystem, call the directory ``cpp-flooblekins/``.
* Please ensure you've used an ``alpine``-based image, or at least a slim one, to keep sizes as small as possible.
  Reference the existing ``Dockerfile``\ s if you need inspiration.
* Please also add some sort of linter or autoformatter for the source code you've written.
  Because Bowtie has code from so many languages in it, it's simply too much to expect any human eyes to catch style or formatting issues.
  Which autoformatter you use will depend on the host language, but if you look at the :gh:`.pre-commit-config.yaml file in this repository <blob/main/.pre-commit-config.yaml>` you'll see we run ``go fmt`` for Golang implementations, ``cargo fmt`` for Rust ones, ``black`` for Python ones, etc., each being a "commonly used" tool in the corresponding language.
  If yours is the first implementation Bowtie supports in a language, use the "most commonly used" linter or autoformatter for the language.
