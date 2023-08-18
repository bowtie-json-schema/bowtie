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
    contributing
    github-actions


Installation
------------

Via Homebrew (macOS or Linuxbrew)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bowtie is available in a `tap <https://docs.brew.sh/Taps>`_ which is located :github:`here <bowtie-json-schema/homebrew-tap>`, and can be installed via:

.. code:: sh

    brew install bowtie-json-schema/tap/bowtie

As a ``shiv`` / ``pyapp``
^^^^^^^^^^^^^^^^^^^^^^^^^

There is an experimental `shiv` of Bowtie published to GitHub on each release.

You can find the :gh:`latest one here <releases/latest/>`.

Once downloading it, run ``chmod +x`` on it and you should be able to use it as-is if you have an existing Python installation.

If you use it (successfully or otherwise) please provide feedback.

Manual Installation via PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bowtie is written in Python, and uses a container runtime to execute JSON Schema implementations, so you'll need both Python and a suitable container runtime installed.

If you have no previous container runtime installed (e.g. Docker), follow the `installation instructions for podman <https://podman.io/docs/installation>`_ specific to your operating system.
Ensure you've started a Podman VM if you are on macOS.

Then follow the `pipx installation process <https://pypa.github.io/pipx/installation/>`_ to install ``pipx``, and finally use it to install Bowtie via:

.. code:: sh

    pipx install bowtie-json-schema

which should give you a working Bowtie installation, which you can check via:

.. code:: sh

    bowtie --help

Further usage details of the command-line interface can be found `here <cli>`.


Execution
---------

In general, executing Bowtie consists of providing 2 pieces of input:

    * The names of one or more supported implementations to execute
    * One or more test cases to run against these implementations (schemas, instances and optionally, expected validation results)

Given these, Bowtie will report on the result of executing each implementation against the input schema/instance pairs.
If expected results are provided, it will compare the results produced against the expected ones, reporting on any implementations which differ from the expected output.

Uses
----

A key use of Bowtie is in executing as input the `official test suite`_ and comparing the results produced by implementations to the expected ones from the suite.

Bowtie however isn't limited to just the test cases in the test suite.
It can be used to compare the validation results of any JSON Schema input across its supported implementations.
