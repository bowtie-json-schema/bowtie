FROM python:3.14.0b3-alpine
WORKDIR /usr/src/myapp
RUN python3 -m pip install fastjsonschema
COPY bowtie_fastjsonschema.py .
CMD ["python3", "bowtie_fastjsonschema.py"]
