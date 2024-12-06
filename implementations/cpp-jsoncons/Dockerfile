FROM alpine:3.21 AS builder

RUN apk add --update-cache git build-base cmake ninja ninja-build curl zip unzip pkgconf && \
    rm -rf /var/cache/apk/*

RUN git clone --branch 2024.04.26 https://github.com/microsoft/vcpkg /app/vcpkg && /app/vcpkg/bootstrap-vcpkg.sh -musl
ENV VCPKG_ROOT=/app/vcpkg
ENV PATH=$VCPKG_ROOT:/usr/lib/ninja-build/bin:$PATH
ENV CMAKE_TOOLCHAIN_FILE=$VCPKG_ROOT/scripts/buildsystems/vcpkg.cmake

WORKDIR /tmp
COPY CMakeLists.txt .
COPY bowtie_jsoncons.cpp .
COPY vcpkg.json .
COPY vcpkg-configuration.json .
RUN vcpkg install

RUN cmake -S /tmp -B /tmp/build -DCMAKE_BUILD_TYPE:STRING=Release -DBUILD_SHARED_LIBS:BOOL=OFF
RUN cmake --build /tmp/build --config Release --parallel 4

FROM alpine:3.21
RUN apk add --no-cache libstdc++ libgcc
COPY --from=builder /tmp/build/bowtie_jsoncons /usr/local/bin/bowtie
CMD [ "bowtie" ]
