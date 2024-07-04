FROM alpine:3.20 AS builder

RUN apk add --no-cache cmake g++ git make

RUN git clone --depth=1 https://github.com/sourcemeta/jsontoolkit.git /tmp/jsontoolkit
RUN cmake -S /tmp/jsontoolkit -B /tmp/build -DCMAKE_BUILD_TYPE:STRING=Release -DBUILD_SHARED_LIBS:BOOL=OFF
RUN cmake --build /tmp/build --config Release --parallel 4
RUN cmake --install /tmp/build --prefix /tmp/dist --config Release --verbose --component sourcemeta_jsontoolkit
RUN cmake --install /tmp/build --prefix /tmp/dist --config Release --verbose --component sourcemeta_jsontoolkit_dev

COPY bowtie_jsontoolkit.cpp /tmp/bowtie.cpp
RUN g++ -O3 -static -std=c++20 -o /tmp/bowtie /tmp/bowtie.cpp \
  -DJSONTOOLKIT_VERSION="\"$(git -C /tmp/jsontoolkit rev-parse --short=8 HEAD)\"" \
  -I/tmp/dist/include -L/tmp/dist/lib \
  -lsourcemeta_jsontoolkit_json \
  -lsourcemeta_jsontoolkit_jsonl \
  -lsourcemeta_jsontoolkit_jsonschema \
  -lsourcemeta_jsontoolkit_jsonpointer \
  -lsourcemeta_jsontoolkit_uri \
  -luriparser

FROM alpine:3.20
COPY --from=builder /tmp/bowtie /usr/local/bin
CMD [ "bowtie" ]
