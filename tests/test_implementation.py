from bowtie._core import Implementation


def test_known():
    assert "python-jsonschema" in Implementation.known()
