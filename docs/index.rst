.. _bowtie:

===============
Bowtie |gitpod|
===============

Bowtie is a *meta*-validator of the `JSON Schema specification <https://json-schema.org/>`_, by which we mean it coordinates executing *other* `validator implementations <https://json-schema.org/implementations.html>`_, collecting and reporting on their results.

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

.. sidebar:: GitPod

   You can use Bowtie immediately without installing it!

   Click below to use it within GitPod, where you'll have immediate access to the Bowtie CLI and all of its supported implementations.

    .. image:: https://gitpod.io/button/open-in-gitpod.svg
      :alt: Open in Gitpod
      :target: https://gitpod.io/#https://github.com/bowtie-json-schema/bowtie


Via Homebrew (macOS or Linuxbrew)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bowtie is available in a `tap <https://docs.brew.sh/Taps>`_ which is located :github:`here <bowtie-json-schema/homebrew-tap>`, and can be installed via:

.. code:: sh

    brew install bowtie-json-schema/tap/bowtie

As a Single Executable
^^^^^^^^^^^^^^^^^^^^^^

There is an experimental `PyApp <https://ofek.dev/pyapp/latest/>`_ of Bowtie published to GitHub on each release.

You can find the :gh:`latest one here <releases/latest/>`.

Once downloading it, run ``chmod +x`` on it and you should be able to use it as-is if you have an existing Python installation.

If you use it (successfully or otherwise) please provide feedback.

Manual Installation via PyPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Bowtie is written in Python, and uses a container runtime to execute JSON Schema implementations, so you'll need both Python and a suitable container runtime installed.

If you have no previous container runtime installed (e.g. Docker), follow the `installation instructions for podman <https://podman.io/docs/installation>`_ specific to your operating system.
Ensure you've started a Podman VM if you are on macOS.

Then follow the `pipx installation process <https://pipx.pypa.io/stable/installation/>`_ to install ``pipx``, and finally use it to install Bowtie via:

.. code:: sh

    pipx install bowtie-json-schema

which should give you a working Bowtie installation, which you can check via:

.. code:: sh

    bowtie --help

Further usage details of the command-line interface can be found `here <cli>`.
