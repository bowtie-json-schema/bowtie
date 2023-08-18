==============================
Using Bowtie in GitHub Actions
==============================

Bowtie can be used from within `GitHub Actions <https://docs.github.com/en/actions/learn-github-actions>`_ by using it in a GitHub workflow step.
For example:

.. code:: yaml

    name: Run Bowtie
    on: [push]

    jobs:
      bowtie:
        runs-on: ubuntu-latest

        steps:
          - name: Install Bowtie
            uses: bowtie-json-schema/bowtie@v2023.08.9

You will likely wish to use the latest version of Bowtie available.

.. seealso::

    `Workflow Syntax for GitHub Actions <https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions>`_

        for full details on writing GitHub Actions workflows

Once you have installed it, the `Bowtie CLI <cli>` will be available in successive run steps.
Most commonly, you can use it to validate an instance (some data) using a specific JSON Schema implementation by adding:

.. code:: yaml

    - name: Validate Schema
      run: bowtie validate -i lua-jsonschema schema.json instance.json

replacing ``lua-jsonschema`` and the filenames with your implementation and schema of choice.
For full details on the commands available, see the `CLI documentation <cli>`.

A fully working example of the above code can also be found :org:`here <github-actions-example>`.
