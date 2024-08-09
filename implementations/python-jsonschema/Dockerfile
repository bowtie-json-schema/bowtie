FROM python:3.12.4-alpine
WORKDIR /usr/src/myapp
ARG IMPLEMENTATION_VERSION
RUN if [[ -z "$IMPLEMENTATION_VERSION" ]] ; then \
        python -m pip install jsonschema ; \
    else \
        python -m pip install jsonschema==$IMPLEMENTATION_VERSION ; \
    fi
COPY bowtie_jsonschema.py .
CMD ["python3", "bowtie_jsonschema.py"]
