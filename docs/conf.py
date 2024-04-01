from pathlib import Path
import importlib.metadata
import re

from bowtie import GITHUB, HOMEPAGE, ORG, REPO

DOCS = Path(__file__).parent
STATIC = DOCS / "_static"

IMPLEMENTATIONS = Path(__file__).parent.parent / "implementations"
IMPLEMENTATION_COUNT = sum(
    1 for path in IMPLEMENTATIONS.iterdir() if not path.name.startswith(".")
)

project = "bowtie"
author = "Julian Berman"
copyright = "2022, " + author

release = importlib.metadata.version("bowtie-json-schema")
version = ".".join(release.split(".")[:3])

language = "en"
default_role = "any"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosectionlabel",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx_click",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    "sphinx_json_schema_spec",
    "sphinx_substitution_extensions",
    "sphinxcontrib.spelling",
    "sphinxext.opengraph",
]

pygments_style = "lovelace"
pygments_dark_style = "one-dark"

html_theme = "furo"
html_logo = str(STATIC / "logo.svg")
html_static_path = [str(STATIC)]
html_theme_options = dict(
    sidebar_hide_name=True,
    # Evade pradyunsg/furo#668
    source_edit_link=str(REPO / "edit/main/docs/") + "{filename}",
)

rst_prolog = f"""
.. |site| replace:: {HOMEPAGE}
.. |version| replace:: {version}

.. |implementation-count| replace:: {IMPLEMENTATION_COUNT}

.. |codespaces| image:: https://github.com/codespaces/badge.svg
    :alt: Open in GitHub Codespaces
    :target: https://codespaces.new{REPO.path}

.. |codespaces-badge| image:: https://github.com/codespaces/badge.svg
    :alt: Open in GitHub Codespaces
    :target: https://codespaces.new{REPO.path}

.. |gitpod| image:: https://gitpod.io/button/open-in-gitpod.svg
    :alt: Open in Gitpod
    :target: https://gitpod.io/#{REPO}

.. |gitpod-badge| image:: https://img.shields.io/badge/Gitpod-try_Bowtie-blue?logo=gitpod
    :alt: Open in Gitpod
    :target: https://gitpod.io/#{REPO}
    :height: 32px


.. _official test suite: https://github.com/json-schema-org/JSON-Schema-Test-Suite

.. _Click Shell Completion Reference: https://click.palletsprojects.com/en/8.1.x/shell-completion/#shell-completion
"""  # noqa: E501, RUF100


def _resolve_broken_refs(app, env, node, contnode):
    # Make `bowtie foo` try `bowtie-foo`, i.e. assume it's a CLI command
    if node["reftarget"].startswith("bowtie "):
        return app.env.get_domain("std").resolve_any_xref(
            env,
            node["refdoc"],
            app.builder,
            node["reftarget"].replace(" ", "-"),
            node,
            contnode,
        )


def setup(app):
    app.connect("missing-reference", _resolve_broken_refs)


def entire_domain(host):
    return r"http.?://" + re.escape(host) + r"($|/.*)"


linkcheck_ignore = [
    entire_domain("img.shields.io"),
    f"{GITHUB}.*#.*",
    "https://gitpod.io/.*#.*",
    str(REPO / "actions"),
    str(REPO / "workflows/CI/badge.svg"),
]

# = Extensions =

# -- autodoc --

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
}

# -- autosectionlabel --

autosectionlabel_prefix_document = True

# -- intersphinx --

intersphinx_mapping = {
    "nox": ("https://nox.thea.codes/en/stable/", None),
    "podman": ("https://docs.podman.io/en/latest", None),
    "pip": ("https://pip.pypa.io/en/stable/", None),
    "python": ("https://docs.python.org/", None),
    "sphinx": ("https://www.sphinx-doc.org", None),
}

# -- extlinks --

extlinks = {
    "gh": (str(REPO) + "/%s", None),
    "github": (str(GITHUB) + "/%s", None),
    "org": (str(ORG) + "/%s", None),
    "issue": (str(REPO / "issues") + "/%s", None),
    "pr": (str(REPO / "pull") + "/%s", None),
    "wiki": ("https://en.wikipedia.org/wiki/%s", None),
}
extlinks_detect_hardcoded_links = True

# -- sphinx-copybutton --

copybutton_prompt_text = r">>> |\.\.\. |\$"
copybutton_prompt_is_regexp = True

# -- sphinxcontrib-spelling --

spelling_word_list_filename = "spelling-wordlist.txt"
spelling_show_suggestions = True
