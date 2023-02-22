FROM rust:1.67-slim AS builder

RUN rustup target add x86_64-unknown-linux-musl
RUN apt update && apt install -y musl-tools musl-dev build-essential gcc-x86-64-linux-gnu
RUN update-ca-certificates

WORKDIR /usr/src/myapp
COPY . .

#ENV RUSTFLAGS='-C linker=x86_64-linux-gnu-gcc'
RUN cargo build --release

FROM debian:bullseye-slim
RUN apt-get update && rm -rf /var/lib/apt/lists/*
COPY --from=builder /usr/src/myapp/target/release/bowtie-rust-boon /usr/local/bin

CMD ["bowtie-rust-boon"]
