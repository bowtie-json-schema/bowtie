# JSON Schema Utils Compiler

The [JSU compiler](https://github.com/zx80/json-schema-utils) converts a
[schema](https://json-schema.org/) to a [model](https://json-model.org/)
internally and then uses [jmc](https://json-model.org/#/JMC) as a backend
to generate a validator in C, Python, JS, Java, PL/pgSQL or Perl.
This implementation run tests with the generated dynamic Python code.

Other backend-supported languages are expected to give the same results,
but should be tested with other bowtie implementations.
Possible discrepancies may derive from regular-expression engine variants,
unimplemented features in some backends, or plain bugs.

## Manual Testing

```sh
docker build --no-cache -t docker.io/zx80/python-jsu -f Dockerfile .
docker build --no-cache --build-arg JMC=dev --build-arg JSU=dev -t docker.io/zx80/python-jsu -f Dockerfile .
docker image ls zx80/python-jsu
docker run --rm --entrypoint /bin/sh -it zx80/python-jsu
bowtie smoke -i docker.io/zx80/python-jsu

for version in 7 6 4 3 2019 2020 ; do
  echo "# version $version"
  bowtie suite -i docker.io/zx80/python-jsu $version > suite_$version.jsonl
  bowtie summary -s failures suite_$version.jsonl
done
```
