from pathlib import Path
import importlib.metadata
import re

from yarl import URL

DOCS = Path(__file__).parent
STATIC = DOCS / "_static"

GITHUB = URL("https://github.com/")
ORG = GITHUB / "bowtie-json-schema"
HOMEPAGE = ORG / "bowtie"

project = "bowtie"
author = "Julian Berman"
copyright = "2022, " + author

release = importlib.metadata.version("bowtie-json-schema")
version = release.partition("-")[0]

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
    "sphinx_json_schema_spec",
    "sphinxcontrib.spelling",
    "sphinxext.opengraph",
]

pygments_style = "lovelace"
pygments_dark_style = "one-dark"

html_theme = "furo"
html_logo = str(STATIC / "dreamed.png")
html_static_path = [str(STATIC)]

rst_prolog = """
.. |site| replace:: https://bowtie.report/

.. _official test suite: https://github.com/json-schema-org/JSON-Schema-Test-Suite
"""  # noqa: E501, RUF100


def entire_domain(host):
    return r"http.?://" + re.escape(host) + r"($|/.*)"


linkcheck_ignore = [
    entire_domain("img.shields.io"),
    f"{GITHUB}.*#.*",
    str(HOMEPAGE / "actions"),
    str(HOMEPAGE / "workflows/CI/badge.svg"),
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
    "shiv": ("https://shiv.readthedocs.io/en/stable", None),
}

# -- extlinks --

extlinks = {
    "gh": (str(HOMEPAGE) + "/%s", None),
    "github": (str(GITHUB) + "/%s", None),
    "org": (str(ORG) + "/%s", None),
}
extlinks_detect_hardcoded_links = True

# -- sphinx-copybutton --

copybutton_prompt_text = r">>> |\.\.\. |\$"
copybutton_prompt_is_regexp = True

# -- sphinxcontrib-spelling --

spelling_word_list_filename = "spelling-wordlist.txt"
spelling_show_suggestions = True
