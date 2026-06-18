# =============================================================================
# Bowtie harness image for IRIS (JSON Schema validator).
#
# Lands at implementations/cpp-iris/Dockerfile in bowtie-json-schema/bowtie.
# The IHOP harness (bowtie_iris.cpp) lives in that directory; this image clones
# IRIS only for the static validator library.
# =============================================================================
FROM alpine:3.22 AS build

RUN apk add --no-cache \
        build-base \
        cmake \
        git \
        re2-dev \
        abseil-cpp-dev

WORKDIR /build
COPY bowtie_iris.cpp CMakeLists.txt ./

ARG IRIS_REF=v0.1.0
RUN git clone --depth 1 --branch "${IRIS_REF}" \
        https://github.com/Cobra007-star-source/IRIS.git iris

RUN cmake -B out -DCMAKE_BUILD_TYPE=Release \
    && cmake --build out --target bowtie_iris -j"$(nproc)"

FROM alpine:3.22
RUN apk add --no-cache libstdc++ re2 abseil-cpp
COPY --from=build /build/out/bowtie_iris /usr/local/bin/bowtie_iris
CMD ["bowtie_iris"]
