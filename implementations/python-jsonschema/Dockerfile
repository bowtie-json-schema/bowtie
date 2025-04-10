FROM python:3.13.3-alpine
WORKDIR /usr/src/myapp
ARG IMPLEMENTATION_VERSION
RUN python -m pip install --no-cache-dir jsonschema${IMPLEMENTATION_VERSION:+==}${IMPLEMENTATION_VERSION} packaging
COPY bowtie_jsonschema.py .
CMD ["python3", "bowtie_jsonschema.py"]
