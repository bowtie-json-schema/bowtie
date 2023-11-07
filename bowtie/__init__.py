"""
A meta-validator for the JSON Schema specification.
"""

from url import URL

HOMEPAGE = URL.parse("https://bowtie.report/")

GITHUB = URL.parse("https://github.com/")
ORG = GITHUB / "bowtie-json-schema"
REPO = ORG / "bowtie"
