===
CLI
===

Bowtie is a versatile tool which you can use to investigate any or all of the implementations it supports.
Below are a few sample command lines you might be interested in.

.. admonition:: Running Commands Against All Implementations

    Many of Bowtie's subcommands take a ``-i / --implementation`` option which specifies which implementations you wish to run against.
    In general, these same subcommands allow repeating this argument multiple times to run across multiple implementations.
    In many or even most cases, you may be interested in running against *all* implementations Bowtie supports.
    For somewhat boring reasons (partially having to do with the GitHub API) this "run against all implementations" functionality is slightly nontrivial to implement in a seamless way, though doing so is nevertheless tracked in :issue:`this issue <24>`.

    In the interim, it's often convenient to use a local checkout of Bowtie in order to list this information.

    Specifically, all supported implementations live in the ``implementations/`` directory, and therefore you can construct a string of ``-i`` arguments using a small bit of shell vomit.
    If you have cloned Bowtie to :file:`/path/to/bowtie` you should be able to use ``$(ls /path/to/bowtie/implementations/ | sed 's/^| /-i /')`` in any command to expand out to all implementations.
    See `below <cli:running the official suite across all implementations>` for a full example.

Examples
--------

Validating a Specific Instance Against One or More Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The `bowtie validate <cli:validate>` subcommand can be used to test arbitrary schemas and instances against any implementation Bowtie supports.

Given some collection of implementations to check -- here perhaps two Javascript implementations -- it takes a single schema and one or more instances to check against it:

.. testcode:: *

    bowtie_validate = 'bowtie validate -i js-ajv -i js-hyperjump <(printf \'{"type": "integer"}\') <(printf 37) <(printf \'"foo"\') | bowtie summary --format pretty'
    print(asyncio.run(run_command(command=bowtie_validate)))

.. testoutput:: *
   :options: +NORMALIZE_WHITESPACE

                                         Bowtie
    ┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Schema              ┃                                                        ┃
    ┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │                     │                                                        │
    │                     │                                 hyperjump-json-sche…   │
    │ {                   │   Instance   ajv (javascript)   (javascript)           │
    │   "type": "integer" │  ────────────────────────────────────────────────────  │
    │ }                   │   37         valid              valid                  │
    │                     │   "foo"      invalid            invalid                │
    │                     │                                                        │
    └─────────────────────┴────────────────────────────────────────────────────────┘
                                      2 tests ran

.. code:: sh

    $ bowtie validate -i js-ajv -i js-hyperjump <(printf '{"type": "integer"}') <(printf 37) <(printf '"foo"')

Note that the schema and instance arguments are expected to be files, and that therefore the above makes use of normal :wiki:`shell process substitution <Process_substitution>` to pass some examples on the command line.

Piping this output to `bowtie summary <cli:summary>` is often the intended outcome (though not always, as you also may upload the output it gives to |site| as a local report).
For summarizing the results in the terminal however, the above command when summarized produces:


.. code:: sh

    $ bowtie validate -i js-ajv -i js-hyperjump <(printf '{"type": "integer"}') <(printf 37) <(printf '"foo"') | bowtie summary
                                         Bowtie
    ┏━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
    ┃ Schema              ┃                                                        ┃
    ┡━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┩
    │                     │                                                        │
    │                     │                                 hyperjump-json-sche…   │
    │ {                   │   Instance   ajv (javascript)   (javascript)           │
    │   "type": "integer" │  ────────────────────────────────────────────────────  │
    │ }                   │   37         valid              valid                  │
    │                     │   "foo"      invalid            invalid                │
    │                     │                                                        │
    └─────────────────────┴────────────────────────────────────────────────────────┘
                                      2 tests ran


Running a Single Test Suite File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the draft 7 ``type``-keyword tests on the Lua ``jsonschema`` implementation, run:

.. testcode:: *

    single_test_suite = 'bowtie suite -i lua-jsonschema https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/type.json | bowtie summary --show failures --format pretty'
    print(asyncio.run(run_command(command=single_test_suite)))

.. testoutput:: *
   :options: +NORMALIZE_WHITESPACE

                        Bowtie
    ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
    ┃ Implementation   ┃ Skips ┃ Errors ┃ Failures ┃
    ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
    │ jsonschema (lua) │ 0     │ 0      │ 2        │
    └──────────────────┴───────┴────────┴──────────┘
                    80 tests ran

.. code:: sh

    $ bowtie suite -i lua-jsonschema https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/type.json | bowtie summary --show failures
                        Bowtie
    ┏━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
    ┃ Implementation   ┃ Skips ┃ Errors ┃ Failures ┃
    ┡━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
    │ jsonschema (lua) │ 0     │ 0      │ 2        │
    └──────────────────┴───────┴────────┴──────────┘
                    80 tests ran


Running the Official Suite Across All Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following will run all Draft 7 tests from the `official test suite`_ (which it will automatically retrieve) across all implementations supporting Draft 7, showing a summary of any test failures.

.. testcode:: *

    draft7_tests = "bowtie suite $(ls implementations/ | sed 's/^/\\-i /') https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/main/tests/draft7 | bowtie summary --show failures --format pretty"
    print(asyncio.run(run_command(command=draft7_tests)))

.. testoutput:: *
   :options: +NORMALIZE_WHITESPACE

                                        Bowtie
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
    ┃ Implementation                                   ┃ Skips ┃ Errors ┃ Failures ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
    │ boon (rust)                                      │ 0     │ 0      │ 0        │
    │ io.openapiprocessor.json-schema-validator (java) │ 0     │ 0      │ 0        │
    │ json-schema-validator (java)                     │ 0     │ 0      │ 0        │
    │ json_schemer (ruby)                              │ 0     │ 0      │ 0        │
    │ jsonschema (python)                              │ 0     │ 0      │ 0        │
    │ jsonschema (go)                                  │ 0     │ 0      │ 0        │
    │ kmp-json-schema-validator (kotlin)               │ 0     │ 0      │ 0        │
    │ JsonSchema.Net (dotnet)                          │ 1     │ 0      │ 0        │
    │ jsonschema (javascript)                          │ 0     │ 10     │ 0        │
    │ hyperjump-json-schema (javascript)               │ 11    │ 0      │ 0        │
    │ jsonschema (rust)                                │ 0     │ 12     │ 6        │
    │ opis-json-schema (php)                           │ 0     │ 20     │ 2        │
    │ vscode-json-language-service (typescript)        │ 0     │ 0      │ 49       │
    │ gojsonschema (go)                                │ 0     │ 20     │ 35       │
    │ jsonschema (lua)                                 │ 0     │ 63     │ 21       │
    │ jsonschemafriend (java)                          │ 0     │ 78     │ 6        │
    │ valijson (c++)                                   │ 0     │ 67     │ 17       │
    │ fastjsonschema (python)                          │ 0     │ 67     │ 31       │
    │ ajv (javascript)                                 │ 0     │ 131    │ 8        │
    └──────────────────────────────────────────────────┴───────┴────────┴──────────┘
                                    906 tests ran

.. code:: sh

    $ bowtie suite $(ls /path/to/bowtie/implementations/ | sed 's/^| /-i /') https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/main/tests/draft7 | bowtie summary --show failures
                                        Bowtie
    ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━┳━━━━━━━━━━┓
    ┃ Implementation                                   ┃ Skips ┃ Errors ┃ Failures ┃
    ┡━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━╇━━━━━━━━━━┩
    │ boon (rust)                                      │ 0     │ 0      │ 0        │
    │ io.openapiprocessor.json-schema-validator (java) │ 0     │ 0      │ 0        │
    │ json-schema-validator (java)                     │ 0     │ 0      │ 0        │
    │ json_schemer (ruby)                              │ 0     │ 0      │ 0        │
    │ jsonschema (python)                              │ 0     │ 0      │ 0        │
    │ jsonschema (go)                                  │ 0     │ 0      │ 0        │
    │ kmp-json-schema-validator (kotlin)               │ 0     │ 0      │ 0        │
    │ JsonSchema.Net (dotnet)                          │ 1     │ 0      │ 0        │
    │ jsonschema (javascript)                          │ 0     │ 10     │ 0        │
    │ hyperjump-json-schema (javascript)               │ 11    │ 0      │ 0        │
    │ jsonschema (rust)                                │ 0     │ 12     │ 6        │
    │ opis-json-schema (php)                           │ 0     │ 20     │ 2        │
    │ vscode-json-language-service (typescript)        │ 0     │ 0      │ 49       │
    │ gojsonschema (go)                                │ 0     │ 20     │ 35       │
    │ jsonschema (lua)                                 │ 0     │ 63     │ 21       │
    │ jsonschemafriend (java)                          │ 0     │ 78     │ 6        │
    │ valijson (c++)                                   │ 0     │ 67     │ 17       │
    │ fastjsonschema (python)                          │ 0     │ 67     │ 31       │
    │ ajv (javascript)                                 │ 0     │ 131    │ 8        │
    └──────────────────────────────────────────────────┴───────┴────────┴──────────┘
                                    906 tests ran


Running Test Suite Tests From Local Checkouts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Providing a local path to the test suite can be used as well, which is useful if you have local changes:

.. code:: sh

    $ bowtie suite $(ls /path/to/bowtie/implementations/ | sed 's/^| /-i /') ~/path/to/json-schema-org/suite/tests/draft2020-12/ | bowtie summary --show failures


Checking An Implementation Functions On Basic Input
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you wish to verify that a particular implementation works on your machine (e.g. if you suspect a problem with the container image, or otherwise aren't seeing results), you can run `bowtie smoke <cli:smoke>`.
E.g., to verify the Golang ``jsonschema`` implementation is functioning, you can run:

.. testcode:: *

    smoke_go_jsonschema = "bowtie smoke -i go-jsonschema --format pretty"
    print(asyncio.run(run_command(command=smoke_go_json)))

.. testoutput:: *
   :options: +NORMALIZE_WHITESPACE

    · allow-everything: ✓✓✓✓✓✓
    · allow-nothing: ✓✓✓✓✓✓

.. code:: sh

   $ bowtie smoke -i go-jsonschema
    · allow-everything: ✓✓✓✓✓✓
    · allow-nothing: ✓✓✓✓✓✓

Reference
---------

.. click:: bowtie._cli:main
   :prog: bowtie
   :nested: full
