# build the image
build:
    docker build -f Dockerfile -t localhost/bowtie-java-openapiprocessor .

# build the image with plain progress
build-plain:
    docker build --no-cache --progress=plain -f Dockerfile -t localhost/bowtie-java-openapiprocessor .

# run smoke test
smoke:
   bowtie smoke -i localhost/bowtie-java-openapiprocessor

# run with draft
suite draft:
    bowtie suite -i localhost/bowtie-java-openapiprocessor {{draft}} -V

# run with draft and create summary
summary draft:
   bowtie suite -i localhost/bowtie-java-openapiprocessor {{draft}} | bowtie summary
