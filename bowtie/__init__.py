"""
A meta-validator for the JSON Schema specification.
"""

from url import URL

HOMEPAGE = URL.parse("https://bowtie.report/")
DOCS = URL.parse("https://docs.bowtie.report/")

GITHUB = URL.parse("https://github.com/")
ORG_NAME = "bowtie-json-schema"
ORG = GITHUB / ORG_NAME
REPO = ORG / "bowtie"
