===
CLI
===

Bowtie is a versatile tool which you can use to investigate any or all of the implementations it supports.
Below are a few sample command lines you might be interested in.

.. admonition:: Running Commands Against All Implementations

    Many of Bowtie's subcommands take a ``-i / --implementation`` option which specifies which implementations you wish to run against.
    In general, these same subcommands allow repeating this argument multiple times to run across multiple implementations.
    In many or even most cases, you may be interested in running against *all* implementations Bowtie supports.
    In the future, Bowtie's CLI will default to running against all implementations in a number of additional cases where it makes sense to do so.

    For now, if you wish to run against all implementations you can make use of the `filter-implementations <cli:filter-implementations>` command to simply output the full list, along with some simple shell vomit to insert the needed ``-i`` options.
    Specifically, running ``$(bowtie filter-implementations | sed 's/^/-i /')`` will expand out to something you can use to run against all implementations.
    See `below <cli:running the official suite across implementations>` for a concrete example.

Examples
--------

Validating a Specific Instance Against One or More Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `bowtie validate <cli:validate>` subcommand can be used to test arbitrary schemas and instances against any implementation Bowtie supports.

Given some collection of implementations to check -- here perhaps two Javascript implementations -- it takes a single schema and one or more instances to check against it:

.. code:: sh

    $ bowtie validate -i js-ajv -i js-hyperjump <(printf '{"type": "integer"}') <(printf 37) <(printf '"foo"')

Note that the schema and instance arguments are expected to be files, and that therefore the above makes use of normal :wiki:`shell process substitution <Process_substitution>` to pass some examples on the command line.

Piping this output to `bowtie summary <cli:summary>` is often the intended outcome (though not always, as you also may upload the output it gives to |site| as a local report).
For summarizing the results in the terminal however, the above command when summarized produces:


.. code:: sh

    $ bowtie validate -i js-ajv -i js-hyperjump <(printf '{"type": "integer"}') <(printf 37) <(printf '"foo"') | bowtie summary

                                                Bowtie
    ┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Schema              ┃                                                                      ┃
    ┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │                     │                                                                      │
    │ {                   │   Instance   hyperjump-json-schema (javascript)   ajv (javascript)   │
    │   "type": "integer" │  ──────────────────────────────────────────────────────────────────  │
    │ }                   │   37         valid                                valid              │
    │                     │   "foo"      invalid                              invalid            │
    │                     │                                                                      │
    └─────────────────────┴──────────────────────────────────────────────────────────────────────┘
                                            2 tests ran


Running the Official Suite Across Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following will run all Draft 7 tests from the `official test suite`_ (which it will automatically retrieve) across all implementations supporting Draft 7, showing a summary of any test failures.

.. code:: sh

    $ bowtie suite $(bowtie filter-implementations | sed 's/^/-i /') draft7 | bowtie summary --show failures


Running a Single Test Suite File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the draft 7 ``type``-keyword tests on the Lua ``jsonschema`` implementation, run:

.. code:: sh

    $ bowtie suite -i lua-jsonschema https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/type.json | bowtie summary --show failures


Running Test Suite Tests From Local Checkouts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Providing a local path to the test suite can be used as well, which is useful if you have additional tests in development locally:

.. code:: sh

    $ bowtie suite $(bowtie filter-implementations | sed 's/^/-i /') ~/path/to/json-schema-org/suite/tests/draft2020-12/ | bowtie summary --show failures


Checking An Implementation Functions On Basic Input
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to verify that a particular implementation works on your machine (e.g. if you suspect a problem with the container image, or otherwise aren't seeing results), you can run `bowtie smoke <cli:smoke>`.
E.g., to verify the Golang ``jsonschema`` implementation is functioning, you can run:

.. code:: sh

   $ bowtie smoke -i go-jsonschema


Connectables
------------

In all of the examples presented above, we passed our desired implementations to Bowtie's ``-i / --implementation`` option.

In truth, this option is more flexible than indicated above, though generally this extra flexibility is useful for more advanced use cases, which this section elaborates on.

The full syntax of the ``-i`` option is known as a *connectable*.

Connectables implement a mini-language for connecting to supported harnesses.

They allow connecting to implementations supported by Bowtie without making assumptions about the specific mechanism used to run or execute them.

In most simple use cases, users likely will not interact directly with the connectable syntax.
Passing ``-i some-supported-implementation`` will generally do The Right Thing™.
But for more advanced usage, the full collection of supported connectables will now be described.

The general syntax for connectables looks like:

    [<kind>:]<id>[:<arguments>*]

The ``kind`` of connectable is optional, and when unspecified defaults to the ``happy`` connectable, making an example of the simplest connectable look like ``lua-jsonschema`` (which expands to ``happy:lua-jsonschema``).
A slightly longer description of what the ``happy`` connectable means is below, but in brief, the ``happy`` connectable will speak *directly* to any implementation which can be imported from Python.
For any *other* implementation, an OCI container will be created (and later destroyed) using the ``image`` connectable.

More generally, the ``id`` is an identifier whose exact form depends on each kind of connectable.
Arguments customize the actual connection to the implementation, and which arguments are supported again depends on the kind of connectable.

Connectables are loosely inspired by `Twisted's strports <twisted:core/howto/endpoints>`.


``image``
^^^^^^^^^

*A container image which Bowtie will start, stop and delete when finished.*

The image ``id`` should be the image name.
Providing a repository is optional, and if unprovided, will default to pulling images from Bowtie's own public repository of images.

The image must be an image whose entrypoint speaks Bowtie's harness protocol (which of course all of Bowtie's own published harnesses images will do).

Examples:

    * ``image:example``: an image named ``example``, retrieved from Bowtie's repository
    * ``example``: with no explicit ``image``, referring to the same image as previous
    * ``image:foo/bar:latest``: an image with fully specified OCI container repository which will be pulled if not already present


``container``
^^^^^^^^^^^^^

*An externally running container which Bowtie will connect to.*

The container must be listening on standard input for input valid under Bowtie's harness protocol.

Bowtie will *not* attempt to manage the container, so this connectable is suitable for cases where you wish to spin up a container externally, leave it running and potentially have Bowtie connect to it multiple times.

The ``id`` is a connector-specific identifier and should indicate the specific intended implementation.
For example, for container images, it must be the name of a container image which will be pulled if needed.
It need not be fully qualified (i.e. include the repository), and will default to pulling from Bowtie's own image repository.

Examples:

    * ``container:deadbeef``: an OCI container with ID ``deadbeef`` which is assumed to be running (and will be attached to)


``direct``
^^^^^^^^^^

*An implementation which is directly importable from Python*

This connectable is useful for implementations Bowtie can speak directly to without inter-process communication.
The list of such implementations is small relative to those reachable using containers.

Examples:

    * ``direct:python-jsonschema``: a direct connection to the Python implementation known as ``jsonschema``


``happy``
^^^^^^^^^

*A connectable which intelligently picks the best possible way to connect to an implementation*

The ``happy`` connectable is a sort of "higher-level" connectable.
Given the name of an implementation, the ``happy`` connectable will pick the *best* possible way to connect to the implementation.
Best here is defined to be "most reliable" and/or "fastest".

Generally this means "connect directly when possible, falling back to spinning up a container".

This connectable is used when no connector is specified, effectively giving the best behavior when no specific connectable is requested.

Examples:

    * ``happy:python-jsonschema``: a direct connection to the Python implementation known as ``jsonschema``, equivalent to ``direct:python-jsonschema``
    * ``happy:some-not-directly-connectable-implementation``: for any non-directly connectable implementation, equivalent to ``image:some-not-directly-connectable-implementation``


Enabling Shell Tab Completion
-----------------------------

The Bowtie CLI supports tab completion using the `click module's built-in support <click:shell-completion>`.
Below are short instructions for your shell using the default configuration paths.

.. tabs::
    .. group-tab:: Bash

        Add this to ``~/.bashrc``:

        .. code:: sh

            $ eval "$(_BOWTIE_COMPLETE=bash_source bowtie)"

    .. group-tab:: Zsh

        Add this to ``~/.zshrc``:

        .. code:: sh

            $ eval "$(_BOWTIE_COMPLETE=zsh_source bowtie)"

    .. group-tab:: Fish

        Add this to ``~/.config/fish/completions/bowtie.fish``:

        .. code:: sh

            $ _BOWTIE_COMPLETE=fish_source bowtie | source

        This is the same file used for the activation script method below. For Fish it's probably always easier to use that method.

Using ``eval`` means that the command is invoked and evaluated every time a shell is started, which can delay shell responsiveness.
To speed it up, write the generated script to a file, then source that.

.. tabs::
    .. group-tab:: Bash

        Save the script somewhere.

        .. code:: sh

            $ _BOWTIE_COMPLETE=bash_source bowtie > ~/.bowtie-complete.bash

        Source the file in ``~/.bashrc``.

        .. code:: sh

            $ . ~/.bowtie-complete.bash

    .. group-tab:: Zsh

        Save the script somewhere.

        .. code:: sh

            $ _BOWTIE_COMPLETE=zsh_source bowtie > ~/.bowtie-complete.zsh

        Source the file in ``~/.zshrc``.

        .. code:: sh

            $ . ~/.bowtie-complete.zsh

    .. group-tab:: Fish

        Save the script to ``~/.config/fish/completions/bowtie.fish``:

        .. code:: sh

            $ _BOWTIE_COMPLETE=fish_source bowtie > ~/.config/fish/completions/bowtie.fish

After modifying your shell configuration, you may need to start a new shell in order for the changes to be loaded.


Reference
---------

.. spelling:word-list::
   perf

.. click:: bowtie._cli:main
   :prog: bowtie
   :nested: full
