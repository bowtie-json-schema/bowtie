FROM python:3.13.0a6-alpine
RUN python -m pip install jsonschema 'referencing-loaders>=0.3.1'
COPY lintsonschema /usr/local/bin
COPY schemas /schemas
CMD ["/usr/local/bin/lintsonschema"]
