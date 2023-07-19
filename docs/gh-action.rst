==============================
Using Bowtie in GitHub Actions
==============================

You can now use bowtie as a GitHub Action. Follow the steps to get started with it in a few simple steps:


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


`This will install bowtie every time you push onto the repository.`

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

    IF THE RUN WAS NOT SUCCESSFUL, YOU WILL SEE A RED CIRCLE WITH A CROSS. RECHECK THE CODE YOU HAVE WRITTEN, AND CORRECT IN CASE OF ANY DISCREPANCY.

`This will help us to test if bowtie is working in the GitHub action.`


Validate using bowtie
---------------------

Now that you have successfully added bowtie to your workflow, let's work on using it to validate your JSON Specifications.

1. Add the ``validate`` Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Add the following code snippet to your YAML file:

.. code:: yaml

        - name: Validate Schema
          run: bowtie validate -i lua-jsonschema schema.json instance.json

Let's break down this command:

* ``bowtie validate``: It tells which command to run.
* ``-i``: It is a required flag for ``validate`` command and specifies which implementation to be used, which in this case is ``lua-jsonschema``.
* ``schema.json``: It is the name of the file containing the defined schema against which instances will be validated.
* ``instance.json``: It is the name of the file containing the instances to be validated. This can also be the path to a directory that contains all the instances.


`You will see that the implementation is skipped and thus does not validate the instances. This is because the lua implementation does not support the default 2020-12 draft.`


2. Change the Dialect
^^^^^^^^^^^^^^^^^^^^^

* To change the dialect used by the implementation, change the validate command to this:

.. code:: yaml

        - name: Validate Schema
          run: bowtie validate -i lua-jsonschema --dialect 7 schema.json instance.json

`This will change the dialect used to draft 7 instead of the default 2020-12.`

3. Use Multiple Implementations
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* You might require using two or more different implementations for the same schema and instances. This is how you can get it done:

.. code:: yaml

        - name: Validate Schema
          run: bowtie validate -i lua-jsonschema -i python-jsonschema schema.json instance.json

`Here we have used just two implementations, namely: python and lua. You may make changes according to your requirements.`


`Note that you cannot use different dialects for different implementations in the same command, bowtie just takes the last dialect specified by using the "--dialect" flag.`
