FROM python:3.11-alpine
WORKDIR /usr/src/myapp
RUN python3 -m pip install jsonschema
COPY bowtie_jsonschema.py .
CMD ["python3", "bowtie_jsonschema.py"]
