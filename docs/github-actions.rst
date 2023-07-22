==============================
Using Bowtie in GitHub Actions
==============================

Bowtie can be used from within GitHub Actions.
Follow the steps to get started with it in a few simple steps:

Setup Bowtie
------------

1. Initial Steps
^^^^^^^^^^^^^^^^

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


*The code snippet will install bowtie every time you push onto the repository.*

2. Verification Steps
^^^^^^^^^^^^^^^^^^^^^

* Append the following code in the already created YAML file:

.. code:: yaml

        - name: Run Bowtie
          run: bowtie --version


* The YAML file will look something like this:

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

            - name: Run Bowtie
              run: bowtie --version

* Push the changes to your repository.
* Go to the ``Actions`` tab of your repository and wait for the action to complete.
* If the run was successful, you will see a green circle with a tick.
* Click on the Workflow and then click on the ``sets-up-bowtie`` Job.
* Open the drop down of the ``Run Bowtie`` step.
* If it shows something like this, bowtie is running successfully:

.. code:: sh

    bowtie, version 2023.6.4

.. admonition:: Note

    IF THE RUN WAS NOT SUCCESSFUL, YOU WILL SEE A RED CIRCLE WITH A CROSS.
    RECHECK THE CODE YOU HAVE WRITTEN, AND CORRECT IN CASE OF ANY DISCREPANCY.

*This will help us to test if bowtie is working in the GitHub action.*


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
refer to the CLI page.

*You will see that the implementation is skipped and thus does not validate the instances.
This is because the lua implementation does not support the default 2020-12 draft.*
