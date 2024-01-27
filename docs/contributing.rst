===================
Contributor's Guide
===================

Thanks for considering contributing to Bowtie, it'd be very much appreciated!


Installation
------------

If you're going to work on Bowtie itself, you likely will want to install it using Python's `editable install functionality <pip:editable-installs>`, e.g. by running:

.. code:: sh

    $ pip install requirements.txt -e .

within a checkout of the Bowtie repository.
This will allow you to make changes to files within Bowtie and see results without reinstalling it repeatedly.


Running the Tests
-----------------

Bowtie has a small set of integration tests which ensure it works correctly on a number of cases.

You can find them in the ``tests/`` directory.

You can run them using `nox <nox:index>`, which you can install using the `linked instructions <nox:tutorial>`.
Once you have done so, you can run:

.. code:: sh

    $ nox -s tests-3.11

to run the tests using Python 3.11 (or any other version you'd like).

There are additional environments which you can have a look through by running ``nox -l``.
Before submitting a PR you may want to run the full suite of tests by running ``nox`` with no arguments to run all of them.
Continuous integration will run them for you regardless, if you don't care to wait.


Running the UI
--------------

Bowtie has a frontend interface used to view or inspect results of Bowtie test runs.

A hosted version of this UI is what powers |site|.
If you are making changes to the UI, you can run it locally by:

    * ensuring you have the `pnpm package manager installed <https://pnpm.io/installation>`_
    * running ``pnpm --dir frontend run start`` from your Bowtie repository checkout, *or* alternatively ``nox -s ui`` to run the same command via ``nox``


For Implementers
----------------

If you have a new (or not so new) implementation which Bowtie doesn't yet support, contributing a test harness to add it is extremely useful (to Bowtie but also hopefully to you!).

See the `harness tutorial <implementers>` for details on writing a harness for your implementation, and please do send a PR to add it!


Proposing Changes
-----------------

If you suspect you may have found a bug, feel free to file an issue after checking whether one already exists.
Of course a pull request to fix it is also very welcome.
Ideally, all pull requests (particularly ones that aren't frontend-focused) should come with tests to ensure the changes work and continue to work.

Continuous integration via GitHub actions should run to indicate whether your change passes both the test suite as well as linters.
Please ensure it passes, or indicate in a comment if you believe it fails spuriously.

Please discuss any larger changes ahead of time for the sake of your own time!
Improvements are very welcome, but large pull requests can be difficult to review or may be worth discussing design decisions before investing a lot of effort.
You're welcome to suggest a change in an issue and thereby get some initial feedback before embarking on an effort that may not get merged.


Improving the Documentation?
----------------------------

Writing good documentation is challenging both to prioritize and to do well.

Any help you may have would be great, especially if you're a beginner who's struggled to understand Bowtie.

Documentation is written in `Sphinx-flavored reStructuredText <sphinx:index>`, so you'll want to at least have a quick look at the `tutorial <sphinx:tutorial>` if you have never written documentation using it.

Feel free to file issues or pull requests as well if you wish something was better documented, as this too can help prioritize.
