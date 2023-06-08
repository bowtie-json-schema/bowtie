FROM python:3.11.4-alpine as builder
RUN apk add --no-cache cargo
ENV CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse
RUN python -m pip wheel --wheel-dir /wheels 'jsonschema>=4.18.0a3'

FROM python:3.11.4-alpine
COPY --from=builder /wheels /wheels
RUN apk add --no-cache libgcc

WORKDIR /usr/src/myapp
RUN python -m pip install --find-links /wheels 'jsonschema>=4.18.0a3' && rm -r /wheels
COPY bowtie_jsonschema.py .
CMD ["python3", "bowtie_jsonschema.py"]
