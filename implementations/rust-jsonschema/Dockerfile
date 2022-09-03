FROM rust:1.63-slim
WORKDIR /usr/src/myapp
COPY . .
RUN cargo install --path .
CMD ["bowtie-rust-jsonschema"]
