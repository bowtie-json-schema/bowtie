from pathlib import Path
import importlib.metadata
import re

from hyperlink import URL

DOCS = Path(__file__).parent
STATIC = DOCS / "_static"

GITHUB = URL.from_text("https://github.com/")
HOMEPAGE = GITHUB.child("bowtie-json-schema", "bowtie")

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

# -- Extension configuration -------------------------------------------------

# -- Options for autodoc extension -------------------------------------------

autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
}

# -- Options for autosectionlabel extension ----------------------------------

autosectionlabel_prefix_document = True

# -- Options for intersphinx extension ---------------------------------------

intersphinx_mapping = {
    "python": ("https://docs.python.org/", None),
}

# -- Options for extlinks extension ------------------------------------------

extlinks = {
    "gh": (str(HOMEPAGE.child("%s")), None),
    "github": (str(GITHUB.child("%s")), None),
    "glossary": ("https://json-schema.org/learn/glossary.html#%s", None),
}

# -- Options for the linkcheck builder ---------------------------------------


def entire_domain(host):
    return r"http.?://" + re.escape(host) + r"($|/.*)"


linkcheck_ignore = [
    entire_domain("codecov.io"),
    entire_domain("img.shields.io"),
    f"{GITHUB}.*#.*",
    str(HOMEPAGE.child("actions")),
    str(HOMEPAGE.child("bowtie/workflows/CI/badge.svg")),
]

# -- Options for spelling extension ------------------------------------------

spelling_show_suggestions = True
