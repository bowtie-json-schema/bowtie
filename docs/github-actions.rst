==============================
Using Bowtie in GitHub Actions
==============================

Bowtie can be used from within `GitHub Actions <https://docs.github.com/en/actions/learn-github-actions>`_ by using it in a GitHub workflow step.
For example:

.. code-block:: yaml
    :substitutions:

    name: Run Bowtie
    on: [push]

    jobs:
      bowtie:
        runs-on: ubuntu-latest

        steps:
          - name: Install Bowtie
            uses: bowtie-json-schema/bowtie@|version|

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

Including Bowtie Output in Workflow summary
-------------------------------------------

Commands such as bowtie summary, bowtie smoke and bowtie info support outputting in markdown format using the
--format markdown flag. This output can be shown in the workflow summary for eg. output validation results for 
a schema + instance as part of a workflow run.

Example:

.. code:: yaml

    - name: Show Report Summary
      run: bowtie suite -i lua-jsonschema https://github.com/json-schema-org/JSON-Schema-Test-Suite/blob/main/tests/draft7/type.json | bowtie summary --format markdown >> $GITHUB_STEP_SUMMARY

.. code:: yaml

    - name: Checking An Implementation Functions On Basic Input
      run: bowtie smoke -i go-jsonschema --format markdown >> $GITHUB_STEP_SUMMARY


A fully working example of the above code can also be found :org:`here <github-actions-example>`.
