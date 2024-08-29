"""
A meta-validator for the JSON Schema specification.
"""

from url import URL

HOMEPAGE = URL.parse("https://bowtie.report/")
DOCS = URL.parse("https://docs.bowtie.report/")

GITHUB = URL.parse("https://github.com/")
ORG = GITHUB / "bowtie-json-schema"
REPO = ORG / "bowtie"

GITHUB_API = URL.parse("https://api.github.com/")
ORG_API = GITHUB_API / "orgs" / "bowtie-json-schema"
PACKAGES_API = ORG_API / "packages"
CONTAINER_PACKAGES_API = PACKAGES_API / "container"
