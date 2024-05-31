from bowtie._core import Dialect


def test_known_latest():
    assert Dialect.latest() in Dialect.known()


def test_latest():
    assert Dialect.latest().pretty_name == "Draft 2020-12"
