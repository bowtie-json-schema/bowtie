.. _bowtie:

======
Bowtie
======

Bowtie is a *meta*-validator of the `JSON Schema specification <https://json-schema.org/>`_, by which we mean it coordinates executing *other* `validator implementations <https://json-schema.org/implementations.html>`_, collecting and reporting on their results.

To do so it defines a simple input/output protocol (specified in `this JSON Schema <https://github.com/bowtie-json-schema/bowtie/blob/main/io-schema.json>`_ which validator implementations can implement, and it provides a CLI which can execute supported implementations.

It's called Bowtie because it fans in lots of JSON then fans out lots of results: ``>·<``.
Looks like a bowtie, no?
Also because it's elegant – we hope.


Contents
--------

.. toctree::
    :maxdepth: 1

    cli
    implementers


Execution
---------

In general, executing Bowtie consists of providing 2 pieces of input:

    * The names of one or more supported implementations to execute
    * One or more test cases to run against these implementations (schemas, instances and optionally, expected validation results)

Given these, Bowtie will report on the result of executing each implementation against the input schema/instance pairs.
If expected results are provided, it will compare the results produced against the expected ones, reporting on any implementations which differ from the expected output.

Uses
----

A key use of Bowtie is in executing as input the `official test suite <https://github.com/json-schema-org/JSON-Schema-Test-Suite>`_ and comparing the results produced by implementations to the expected ones from the suite.

Bowtie however isn't limited to just the test cases in the test suite.
It can be used to compare the validation results of any JSON Schema input across its supported implementations.
