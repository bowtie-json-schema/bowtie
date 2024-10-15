FROM alpine:3.20 AS builder

RUN apk add --no-cache cmake g++ git make

RUN git clone --depth=1 https://github.com/sourcemeta/blaze.git /tmp/blaze
RUN cmake -S /tmp/blaze -B /tmp/build -DCMAKE_BUILD_TYPE:STRING=Release -DBUILD_SHARED_LIBS:BOOL=OFF
RUN cmake --build /tmp/build --config Release --parallel 4
RUN cmake --install /tmp/build --prefix /tmp/dist --config Release --verbose --component sourcemeta_jsontoolkit
RUN cmake --install /tmp/build --prefix /tmp/dist --config Release --verbose --component sourcemeta_jsontoolkit_dev
RUN cmake --install /tmp/build --prefix /tmp/dist --config Release --verbose --component sourcemeta_blaze
RUN cmake --install /tmp/build --prefix /tmp/dist --config Release --verbose --component sourcemeta_blaze_dev

COPY bowtie_blaze.cpp /tmp/bowtie.cpp
RUN g++ -O3 -static -std=c++20 -o /tmp/bowtie /tmp/bowtie.cpp \
  -DBLAZE_VERSION="\"$(git -C /tmp/blaze rev-parse --short=8 HEAD)\"" \
  -I/tmp/dist/include -L/tmp/dist/lib \
  -lsourcemeta_jsontoolkit_json \
  -lsourcemeta_jsontoolkit_jsonl \
  -lsourcemeta_jsontoolkit_jsonschema \
  -lsourcemeta_jsontoolkit_jsonpointer \
  -lsourcemeta_jsontoolkit_uri \
  -lsourcemeta_blaze_compiler \
  -lsourcemeta_blaze_evaluator \
  -luriparser

FROM alpine:3.20
COPY --from=builder /tmp/bowtie /usr/local/bin
CMD [ "bowtie" ]
