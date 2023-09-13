===
CLI
===

Examples
--------

Running a Single Test Suite File
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To run the draft 7 ``type``-keyword tests on the Lua ``jsonschema`` implementation, run:

.. code:: sh

    $ bowtie suite -i lua-jsonschema https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/type.json | bowtie summary --show failures


Running the Official Suite Across All Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The following will run all Draft 7 tests from the `official test suite`_ (which it will automatically retrieve) across all implementations supporting Draft 7, and generate an HTML report named :file:`bowtie-report.html` in the current directory:

.. code:: sh

    $ bowtie suite $(find /path/to/bowtie/checkout/implementations/ -mindepth 1 -maxdepth 1 -type d | sed 's/.*\/implementations\//-i /') https://github.com/json-schema-org/JSON-Schema-Test-Suite/tree/main/tests/draft7 | bowtie summary --show failures


Running Test Suite Tests From Local Checkouts
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Providing a local path to the test suite can be used as well, which is useful if you have local changes:

.. code:: sh

    $ bowtie suite $(find /path/to/bowtie/checkout/implementations/ -mindepth 1 -maxdepth 1 -type d | sed 's/.*\/implementations\//-i /') ~/path/to/json-schema-org/suite/tests/draft2020-12/ | bowtie summary --show failures


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
