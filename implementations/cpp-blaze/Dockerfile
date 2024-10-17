FROM alpine:3.20 AS builder

RUN apk add --no-cache cmake g++ git make

RUN git clone https://github.com/sourcemeta/blaze.git /tmp/blaze

# Pin a specific commit for stable builds
RUN git -C /tmp/blaze checkout 43cac42dc486be24addbc2cd0aa646d18e2000f5

COPY CMakeLists.txt /tmp/CMakeLists.txt
COPY bowtie_blaze.cpp /tmp/bowtie_blaze.cpp

RUN cmake -S /tmp -B /tmp/build -DCMAKE_BUILD_TYPE:STRING=Release -DBUILD_SHARED_LIBS:BOOL=OFF
RUN cmake --build /tmp/build --config Release --parallel 4

FROM alpine:3.20
RUN apk add --no-cache libstdc++ libgcc
COPY --from=builder /tmp/build/bowtie_blaze /usr/local/bin/bowtie
CMD [ "bowtie" ]
