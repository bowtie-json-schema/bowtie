from bowtie._core import Dialect


def test_latest():
    assert max(Dialect.known()).pretty_name == "Draft 2020-12"
