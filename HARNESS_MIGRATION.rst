====
Migrate test harness to a separate repository
====

The document describes steps required to move a test harness from ``bowtie`` repository
to a dedicated repository (e.g. `kotlin-kmp-json-schema-validator <https://github.com/bowtie-json-schema/kotlin-kmp-json-schema-validator>`_).

+++++
Create dedicated repository
+++++

First of all, you need to create a dedicated repository for the test harness.
The repository can be created using the template repository: TBD.
// TODO(optimumcode): create a template repository

**The repository name MUST exactly match the test harness name in bowtie**.

If you are a member of `Bowtie <https://github.com/bowtie-json-schema>`_ organization
you can create a new repository directly in the organization.
If you are not a member of the organization you can create the repository under your profile
and once the test harness is migrated, you can move a repository to the **Bowtie** organization
(kindly create a task for that in `bowtie <https://github.com/bowtie-json-schema/bowtie/issues/new/choose>`_ project).

++++
Move the test harness to a new repository
++++

We want to preserve the git history for a test harness.
To achieve that, we use `git-filter-repo <https://github.com/newren/git-filter-repo>`_.
Ensure you have `python and git versions <https://github.com/newren/git-filter-repo?tab=readme-ov-file#prerequisites>`_
compatible with the ``git-filter-repo``.

If you use ``pipx`` you can install it using the following command ::

    pipx install git-filter-repo==v2.45.0

NOTE: there were some issues with the latest version 2.47.0.
It should be `fixed <https://github.com/newren/git-filter-repo/commit/4697eeb37b7c3c30b0492e344f6b89f7139cef26>`_ in the next version.

Once ``git-filter-repo`` is installed, we can proceed with moving the test harness:

#. Copy bowtie and newly created repository to you local machine;
#. Create an environment variable containing the test harness name ::

    TEST_HARNESS=<test harness name>
    # e.g.
    # TEST_HARNESS=kotlin-kmp-json-schema-validator

#. Execute the following command to copy the git history related to the test harness
   to a new repository ::

    git-filter-repo --refs main \
     --source ./bowtie/ \
     --target ./$TEST_HARNESS/ \
     --subdirectory-filter implementations/$TEST_HARNESS/ \
     --refname-callback '
      # Change e.g. refs/heads/master to refs/heads/prefix-master
      rdir,rpath = os.path.split(refname)
      return rdir + b"/bowtie-" + rpath'

#. After the previous command, the new test harness repo will have two branches:

   * main - default repository branch
   * bowtie-main - branch containing the history from bowtie repository

   Those branches does not have anything in common and git will not allow merging them by default.
   Switch to the main branch in the new test harness repository and execute the following command ::

    git merge --allow-unrelated-histories bowtie-main

#. Move pre-commit and dependabot configurations specific to the test harness from bowtie repository to new test harness repository.
   Commit those changes to the main branch.

#. Enable QEMU (if test harness does not support cross-arch compilation) or disable it (if test harness supports cross-arch compilation). TBD.

#. Add a ``.gitignore`` file if needed.

#. Push the main branch to the remote repository

++++
Remove test harness from bowtie repository
++++
