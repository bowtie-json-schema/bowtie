FROM rust:1.86-slim AS builder

RUN rustup target add x86_64-unknown-linux-musl
RUN apt update && apt install -y musl-tools musl-dev build-essential gcc-x86-64-linux-gnu
RUN update-ca-certificates

WORKDIR /usr/src/myapp
COPY . .

ENV RUSTFLAGS='-C linker=x86_64-linux-gnu-gcc'
ENV CARGO_INCREMENTAL=0
ENV CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse
RUN cargo build --target x86_64-unknown-linux-musl --release

FROM alpine
COPY --from=builder /usr/src/myapp/target/x86_64-unknown-linux-musl/release/bowtie-rust-boon /usr/local/bin

CMD ["bowtie-rust-boon"]
