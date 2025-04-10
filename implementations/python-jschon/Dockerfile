FROM python:3.13.3-alpine
WORKDIR /usr/src/myapp
RUN python3 -m pip install jschon
COPY bowtie_jschon.py .
CMD ["python3", "bowtie_jschon.py"]
