.. _bowtie:

=========================
Bowtie |codespaces-badge|
=========================

Bowtie is a *meta*-validator of the `JSON Schema specification <https://json-schema.org/>`_, by which we mean it coordinates executing *other* `validator implementations <https://json-schema.org/implementations>`_, collecting and reporting on their results.

It has a few parts:

    * a command line tool which can be used to access any of the |implementation-count| :github:`JSON Schema implementations <orgs/bowtie-json-schema/packages>` integrated with it. Use it to validate any schema and instance against any implementation.
    * a report, accessible at |site|, showing how well each implementation complies with the specification and which tests they fail (if any)
    * a protocol which new implementations can integrate with in order to have their implementation be supported by Bowtie

It's called Bowtie because it fans in lots of JSON then fans out lots of results: ``>·<``.
Looks like a bowtie, no?
Also because it's elegant – we hope.

If you're just interested in how implementations stack up against each other, you can find the most up to date report at |site|.


.. toctree::
  :hidden:

  cli
  github-actions
  contributing
  implementers


Installation
------------

.. sidebar:: Jump Right In!

   You can use Bowtie immediately without installing it!

   :github:`GitHub Codespaces <features/codespaces>` can provide you with an immediate, fully-working cloud environment with Bowtie and all of its supported implementations installed into it:

   |codespaces|


Via Homebrew (macOS or Linuxbrew)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bowtie is available in a `tap <https://docs.brew.sh/Taps>`_ which is located :github:`here <bowtie-json-schema/homebrew-tap>`, and can be installed via:

.. code:: sh

    brew install bowtie-json-schema/tap/bowtie

Manual Installation via PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bowtie is written in Python, and uses a container runtime to execute JSON Schema implementations, so you'll need both Python and a suitable container runtime installed.

If you have no previous container runtime installed (e.g. Docker), follow the `installation instructions for podman <https://podman.io/docs/installation>`_ specific to your operating system.
Ensure you've started a Podman VM if you are on macOS.

Then follow the `uv installation process <https://docs.astral.sh/uv/getting-started/installation/>`_ to install ``uv``, and finally use it to run Bowtie via:

.. code:: sh

    uvx --from bowtie-json-schema bowtie --help

which should show you Bowtie's help by invoking its command line interface.
You can install it so it is runnable via simply ``bowtie`` by using ``uv tool install bowtie-json-schema``.

Further usage details of the command-line interface can be found `here <cli>`.
