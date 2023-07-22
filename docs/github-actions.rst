==============================
Using Bowtie in GitHub Actions
==============================

Bowtie can be used from within GitHub Actions.
Follow the steps to get started with it in a few simple steps:

Setup Bowtie
------------

* Create ``.github/workflows`` directory in your repository.
* Create a file with ``.yml`` extension.
* Enter the following code in the YAML file:

.. code:: yaml

    name: Setup Bowtie
    run-name: ${{ github.actor }} is learning to use Bowtie

    on: [push]

    jobs:
    sets-up-bowtie:
        runs-on: ubuntu-latest

        steps:
        - name: Install Bowtie
            uses: bowtie-json-schema/bowtie@v2023.05.12

* Push the changes to your repository.

*The code snippet will install bowtie every time you push onto the repository.*

Validate using bowtie
---------------------

Now that you have successfully added bowtie to your workflow,
let's work on using it to validate your JSON Specifications.

Add the ``validate`` Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Add the following code snippet to your YAML file:

.. code:: yaml

        - name: Validate Schema
          run: bowtie validate -i lua-jsonschema schema.json instance.json

For breakdown of this command,
refer to the :doc:`CLI <cli>` page.
