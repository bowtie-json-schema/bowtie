==================================
Tutorial: Adding An Implementation
==================================


The purpose of Bowtie is to support a large number of JSON Schema implementations and provide ways to collect their output for comparison to others.

If you've written an implementation of JSON Schema, let's see how you can add support for it to Bowtie.


Prerequisites
-------------

* `bowtie` itself, already installed
* A target JSON Schema implementation, which you do not necessarily need installed locally on your machine
* `docker <https://www.docker.com/>`_, `podman <https://podman.io/>`_ or a similarly compatible tool for building OCI container images and running OCI containers

Beyond the above, your first step is to ensure you're familiar with the implementation you're about to add support for, as well as its host language (the language it's written to be used from).
If you're its author, you're certainly well qualified :) -- if not, you'll see a few things below which you'll need to find in its API documentation, such as what function(s) or object(s) you use to validate :term:`instances <instance>` under :term:`schemas <schema>`.


First Overview
--------------

Bowtie essentially orchestrates running a number of containers, passing incoming test cases (schemas and instances) to each one of them, and then collecting, comparing and rendering the results.
To do so it speaks two protocols -- one which deals with the structure of incoming test cases provided at the command line (which we won't discuss much in this document) and a second which it uses to communicate bidirectionally with each implementation (which we will discuss in detail here).

Any JSON Schema implementation will have some way of getting schemas and instances "into" it.
This core API is what we'll wrap in a docker image, and orchestrate having it called correctly with cases that bowtie sends over standard input.
It should write its results to standard output, which bowtie will collect (and possibly compare to other implementations).


Submitting Your Implementation Upstream
---------------------------------------

If the implementation you've added isn't already supported by Bowtie, contributing it is very welcome!

Please feel free to :gh:`open an issue <issues/new>` or :gh:`pull request <compare>` adding it to the :gh:`implementations directory <tree/main/implementations>`.
