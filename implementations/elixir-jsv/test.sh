#!/usr/bin/bash -ev
trap exit INT

docker build --progress plain -t localhost/jsv-bowtie .

docker run --rm -i localhost/jsv-bowtie <<EOF
{"cmd": "start", "version": 1}
{"cmd": "dialect", "dialect": "https://json-schema.org/draft/2020-12/schema" }
{"cmd": "run", "seq": 11, "case": {"description": "test case 1", "schema": {}, "tests": [{"description": "a test", "instance": {}}] }}
{"cmd": "run", "seq": 11, "case": {"description": "test case 2", "schema": {"const": 37}, "tests": [{"description": "not 37", "instance": {}}, {"description": "is 37", "instance": 37}] }}
{"cmd": "stop"}
EOF

bowtie smoke -i localhost/jsv-bowtie
bowtie suite -x -i localhost/jsv-bowtie draft2020-12 | bowtie summary --show failures
bowtie suite -x -i localhost/jsv-bowtie draft7       | bowtie summary --show failures
