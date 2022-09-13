FROM rust:1.63-slim AS builder

RUN rustup target add x86_64-unknown-linux-musl
RUN apt update && apt install -y musl-tools musl-dev build-essential gcc-x86-64-linux-gnu
RUN update-ca-certificates

WORKDIR /usr/src/myapp
COPY . .

ENV RUSTFLAGS='-C linker=x86_64-linux-gnu-gcc'
RUN cargo build --target x86_64-unknown-linux-musl --release

FROM alpine
COPY --from=builder /usr/src/myapp/target/x86_64-unknown-linux-musl/release/bowtie-rust-jsonschema /usr/local/bin

CMD ["bowtie-rust-jsonschema"]
