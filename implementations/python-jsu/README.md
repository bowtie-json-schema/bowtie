# JSON Schema Utils Compiler

The [JSU compiler](https://github.com/zx80/json-schema-utils) converts a
[schema](https://json-schema.org/) to a [model](https://json-model.org/)
internally and then uses [jmc](https://json-model.org/#/JMC) as a backend
to generate a validator in C, Python, JS, Java, PL/pgSQL or Perl.

All backend-supported languages are _expected_ to give the same results.
Possible discrepancies may derive from regular-expression engine variants,
unimplemented/unsupported features in some backends or JSON implementations,
or plain bugs.

## Manual Testing

```sh
JSU_CONTAINER=docker.io/zx80/bowtie-jsu
docker build --no-cache -t $JSU_CONTAINER -f Dockerfile .
docker build --no-cache --build-arg JMC=dev --build-arg JSU=dev -t $JSU_CONTAINER -f Dockerfile .
docker image ls $JSU_CONTAINER
docker run --rm --entrypoint /bin/sh -it $JSU_CONTAINER
bowtie smoke -i $JSU_CONTAINER

for version in 7 6 4 3 2019 2020 ; do
  echo "# version $version"
  bowtie suite -i $JSU_CONTAINER $version > suite_$version.jsonl
  bowtie summary -s failures suite_$version.jsonl
done
```
