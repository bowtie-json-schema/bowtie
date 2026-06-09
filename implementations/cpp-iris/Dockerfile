# =============================================================================
# Bowtie harness image for IRIS (JSON Schema validator).
#
# This is the file that lands at implementations/cpp-iris/Dockerfile in the
# bowtie-json-schema/bowtie repository. It clones IRIS, builds only the static
# `iris` library plus the `bowtie_iris` IHOP harness, and runs the harness as
# the container entrypoint. Bowtie then drives it over stdio.
#
# Minimal build: gateway / simdjson / examples / tests / JIT are all OFF. The
# slow-path validator (which carries IRIS's draft-2020-12 conformance) links
# RE2 for linear-time, ReDoS-safe pattern/format evaluation.
# =============================================================================
FROM alpine:3.22 AS build

RUN apk add --no-cache \
        build-base \
        cmake \
        git \
        re2-dev \
        abseil-cpp-dev

WORKDIR /src
# Pinned to a release tag so bowtie.report results map to a fixed snapshot.
# Override with --build-arg IRIS_REF=<branch|tag> to test other revisions.
ARG IRIS_REF=v0.1.0
RUN git clone --depth 1 --branch "${IRIS_REF}" \
        https://github.com/Cobra007-star-source/IRIS.git .

RUN cmake -B build \
        -DCMAKE_BUILD_TYPE=Release \
        -DIRIS_ENABLE_LTO=OFF \
        -DIRIS_BUILD_SIMDJSON=OFF \
        -DIRIS_BUILD_GATEWAY=OFF \
        -DIRIS_BUILD_TESTS=OFF \
        -DIRIS_BUILD_EXAMPLES=OFF \
        -DIRIS_BUILD_BENCHMARKS=ON \
        -DIRIS_BUILD_BOWTIE=ON \
        -DIRIS_ENABLE_JIT=OFF \
    && cmake --build build --target bowtie_iris

# -----------------------------------------------------------------------------
# Runtime image: just the harness binary + RE2/abseil/libstdc++ runtimes.
# -----------------------------------------------------------------------------
FROM alpine:3.22
RUN apk add --no-cache libstdc++ re2 abseil-cpp
COPY --from=build /src/build/bench/bowtie_iris /usr/local/bin/bowtie_iris
CMD ["bowtie_iris"]
