FROM python:3.10-alpine
RUN python -m pip install jsonschema
COPY lintsonschema /usr/bin
COPY io-schema.json /
CMD ["/usr/bin/lintsonschema"]
