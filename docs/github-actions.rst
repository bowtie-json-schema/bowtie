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

A fully working example of the above code can also be found :org:`here <github-actions-example>`.


Including Bowtie Output in a Workflow Summary
---------------------------------------------

Some of Bowtie's commands, notably `bowtie summary <cli:summary>`, support outputting in markdown format using the `--format markdown <bowtie summary --format>` option.
This can be useful for including their output in GitHub Actions' workflow summaries, e.g. to show validation results within the GitHub UI.

For example:

.. code:: yaml

    - name: Validate 37 is an Integer
      run: |
        bowtie validate -i python-jsonschema <(printf '{"type": "integer"}') <(printf '37') | bowtie summary --format markdown >> $GITHUB_STEP_SUMMARY

.. code:: yaml

    - name: Smoke Test a Bowtie Implementation
      run: bowtie smoke -i go-jsonschema --format markdown >> $GITHUB_STEP_SUMMARY

.. seealso::

    `Displaying a Workflow Job's Summary <https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#adding-a-job-summary>`_

        for further details on ``GITHUB_STEP_SUMMARY``
