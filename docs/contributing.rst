===================
Contributor's Guide
===================

Thanks for considering contributing to Bowtie, it'd be very much appreciated!


Installation
------------

If you're going to work on Bowtie itself, you likely will want to install it using Python's `editable install functionality <pip:editable-installs>`, as well as to install Bowtie's testing dependencies e.g. by running:

.. code:: sh

    $ uv pip install -r test-requirements.txt -e .

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

Please also feel free to ask for commit rights on Bowtie's repository, if only to work on your own implementation's harness -- there's no intention to gate-keep the test harness for your implementation, so while there *is* an intentional level of homogeneity that should be kept with other harnesses, there's nonetheless a desire for development to be more open than closed.


Proposing Changes
-----------------

What It Means to Contribute
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Before mentioning a few tips about contributions, it's important to make very clear what it means to submit a contribution to Bowtie.

Bowtie is open source software, licensed under the MIT license.
By submitting code or making a contribution of any kind you are *implicitly agreeing to license your contributed work under this license forever, just as Bowtie itself already is*.
If you do not agree to do so you must say so explicitly, though doing so likely will mean your contribution won't be accepted.
Furthermore by doing so you are also implicitly asserting you have the *right to do this* -- in particular, if you have an employer and have done any portion of this work as part of your employment, you are asserting that you are able to grant these licensing terms yourself, and that your employer does not in some way own the rights themselves, and/or you assert that you have explicitly gotten permission from your employer.

None of the above should be meaningfully different from your experience with any other open source project, but occasionally new contributors may not fully understand the implications of making contributions.

(The above is of course not legal advice, nor is it a comprehensive list nor guide on what rights you are expected to have and grant when submitting pull requests.)

*You may not use any large language model of any kind as part of assembling your contribution.*
This includes GitHub Copilot, ChatGPT or any other vendor's product(s).
You may not have these models produce part of your contribution and then modify it.
Any attempt to submit code generated with the help of these models will result in a ban from Bowtie's repository and the removal of your contributions.

If you are curious about the reasoning for the above, it has to do with the unclear copyright status of these models' training sets, and thereby the unclear status of code they produce, which may be regurgitated from copyrighted works.
Whether these technologies are revolutionary or not, for contributions' sake, they are not allowed.

Found a Bug?
^^^^^^^^^^^^

If you suspect you may have found a bug, feel free to file an issue after checking whether one already exists.
Of course a pull request to fix it is also very welcome.
Ideally, all pull requests (particularly ones that aren't frontend-focused) should come with tests to ensure the changes work and continue to work.

Continuous integration via GitHub actions should run to indicate whether your change passes both the test suite as well as linters.
Please ensure it passes, or indicate in a comment if you believe it fails spuriously.

Please discuss any larger changes ahead of time for the sake of your own time!
Improvements are very welcome, but large pull requests can be difficult to review or may be worth discussing design decisions before investing a lot of effort.
You're welcome to suggest a change in an issue and thereby get some initial feedback before embarking on an effort that may not get merged.


Improving the Documentation?
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Writing good documentation is challenging both to prioritize and to do well.

Any help you may have would be great, especially if you're a beginner who's struggled to understand Bowtie.

Documentation is written in `Sphinx-flavored reStructuredText <sphinx:index>`, so you'll want to at least have a quick look at the `tutorial <sphinx:tutorial>` if you have never written documentation using it.

Feel free to file issues or pull requests as well if you wish something was better documented, as this too can help prioritize.


Building the Documentation Locally
==================================

The code for the documentation is in the :gh:`docs directory of the Bowtie repository <tree/main/docs>`.

You can build the documentation locally by running the following command from the root of the repository

.. code:: sh

    $ nox -s "docs(dirhtml)" -- dirhtml

which will generate a directory called ``dirhtml`` containing the built HTML.


Improving the Contributor's Guide Itself
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Please feel free to share difficulties you had with developing on Bowtie itself.
This contributor's guide is *not* meant to be a complete beginner's guide -- e.g. it will not teach you how to do things which are common across all Python projects (let alone teach you Python itself).
While there's no intention for it to become such a beginner's guide, it *is* completely reasonable for it to contain links to *other guides* which can help.
So if you had trouble doing something in particular, please feel free to send a pull request to modify this guide, especially if you still cannot figure out how to do it.



Triage & PR Review
^^^^^^^^^^^^^^^^^^

There are a number of oft-overlooked ways you can help Bowtie's development.

One in particular is helping to either triage issues (e.g. attempting to reproduce an issue someone has reported, and commenting saying you can reproduce, or even better, that you see where the issue lies).

Another is helping to review pull requests!
Being a good reviewer is an important skill and also a way you can save someone else time reviewing!


Have a Question?
----------------

Please do not use the issue tracker for questions, it's reserved for things believed to be bugs, or new functionality, but please *do* feel free to open :gh:`GitHub discussions on Bowtie's discussion tab <discussions>`.
Any help you can offer to answer others' questions is of course appreciated as well.
You are also welcome to ask questions on the JSON Schema Slack.
