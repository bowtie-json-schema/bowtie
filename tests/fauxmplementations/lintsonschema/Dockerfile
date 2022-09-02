FROM python:3.10-slim
RUN python -m pip install jsonschema
COPY lintsonschema /usr/bin
COPY io-schema.json /
CMD ["/usr/bin/lintsonschema"]
