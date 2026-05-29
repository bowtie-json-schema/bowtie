FROM rust:1.96-slim AS builder

RUN ARCH=$(dpkg --print-architecture) && \
    case "$ARCH" in \
      amd64) \
        echo x86_64-unknown-linux-musl > /tmp/rust-target; \
        echo x86_64-linux-gnu-gcc > /tmp/linker; \
        echo gcc-x86-64-linux-gnu > /tmp/gcc-pkg ;; \
      arm64) \
        echo aarch64-unknown-linux-musl > /tmp/rust-target; \
        echo aarch64-linux-gnu-gcc > /tmp/linker; \
        echo gcc-aarch64-linux-gnu > /tmp/gcc-pkg ;; \
      *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    rustup target add $(cat /tmp/rust-target) && \
    apt update && apt install -y musl-tools musl-dev build-essential $(cat /tmp/gcc-pkg)
RUN update-ca-certificates

WORKDIR /usr/src/myapp
COPY . .

ENV CARGO_INCREMENTAL=0
ENV CARGO_REGISTRIES_CRATES_IO_PROTOCOL=sparse
RUN RUSTFLAGS="-C linker=$(cat /tmp/linker)" \
    cargo build --target $(cat /tmp/rust-target) --release && \
    cp target/$(cat /tmp/rust-target)/release/bowtie-rust-jsonschema /usr/local/bin/

FROM alpine
COPY --from=builder /usr/local/bin/bowtie-rust-jsonschema /usr/local/bin

CMD ["bowtie-rust-jsonschema"]
