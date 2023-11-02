===
CLI
===

Examples
--------

.. sidebar::

    Many of Bowtie's subcommands take a ``-i / --implementation`` option which specifies which implementations you wish to run against.
    In general, these same subcommands allow repeating this argument multiple times to run across multiple implementations.
    In many or even most cases, you may be interested in running against *all* implementations Bowtie supports.
    For somewhat boring reasons partially having to do with the GitHub API, this turns out to be nontrivial to implement, though it is tracked in :issue:`this issue <24>`.
    In the interim, it's often convenient to use a local checkout of Bowtie in order to list this information.
    Specifically, all supported implementations live in the ``implementations/`` directory, and therefore you can construct a string of ``-i`` arguments using a small bit of shell vomit.
    If you have cloned Bowtie to :file:`/path/to/bowtie` you should be able to use ``$(ls /path/to/bowtie/implementations/ | sed 's/^| /-i /')`` in any command to expand out to all implementations.
    See `below <cli:running the official suite across all implementations>` for a full example.

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
    2023-11-02 15:43.10 [debug    ] Will speak                     dialect=https://json-schema.org/draft/2020-12/schema
    2023-11-02 15:43.10 [info     ] Finished                       count=1
                                            Bowtie
    ┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Schema              ┃                                                              ┃
    ┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │                     │                                                              │
    │ {                   │   Instance   ajv (javascript)   hyperjump-jsv (javascript)   │
    │   "type": "integer" │  ──────────────────────────────────────────────────────────  │
    │ }                   │   37         valid              valid                        │
    │                     │   "foo"      invalid            invalid                      │
    │                     │                                                              │
    └─────────────────────┴──────────────────────────────────────────────────────────────┘
                                        2 tests ran


Running a Single Test Suite File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the draft 7 ``type``-keyword tests on the Lua ``jsonschema`` implementation, run:

.. code:: sh

    $ bowtie suite -i lua-jsonschema https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/type.json | bowtie summary --show failures


Running the Official Suite Across All Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following will run all Draft 7 tests from the `official test suite`_ (which it will automatically retrieve) across all implementations supporting Draft 7, and generate an HTML report named :file:`bowtie-report.html` in the current directory:

.. code:: sh

    $ bowtie suite $(ls /path/to/bowtie/implementations/ | sed 's/^| /-i /') https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/main/tests/draft7 | bowtie summary --show failures


Running Test Suite Tests From Local Checkouts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Providing a local path to the test suite can be used as well, which is useful if you have local changes:

.. code:: sh

    $ bowtie suite $(ls /path/to/bowtie/implementations/ | sed 's/^| /-i /') ~/path/to/json-schema-org/suite/tests/draft2020-12/ | bowtie summary --show failures


Checking An Implementation Functions On Basic Input
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to verify that a particular implementation works on your machine (e.g. if you suspect a problem with the container image, or otherwise aren't seeing results), you can run `bowtie smoke <cli:smoke>`.
E.g., to verify the Golang ``jsonschema`` implementation is functioning, you can run:

.. code:: sh

   $ bowtie smoke -i go-jsonschema


Reference
---------

.. click:: bowtie._cli:main
   :prog: bowtie
   :nested: full
