FROM alpine:3.21 AS builder

RUN apk add --no-cache cmake g++ git make

RUN git clone https://github.com/sourcemeta/blaze.git /tmp/blaze

# Pin a specific commit for stable builds
RUN git -C /tmp/blaze checkout 0424f5765c4c18162a7f7ed8354134e680f6664e

COPY CMakeLists.txt /tmp/CMakeLists.txt
COPY bowtie_blaze.cpp /tmp/bowtie_blaze.cpp

RUN cmake -S /tmp -B /tmp/build -DCMAKE_BUILD_TYPE:STRING=Release -DBUILD_SHARED_LIBS:BOOL=OFF
RUN cmake --build /tmp/build --config Release --parallel 4

FROM alpine:3.21
RUN apk add --no-cache libstdc++ libgcc
COPY --from=builder /tmp/build/bowtie_blaze /usr/local/bin/bowtie
CMD [ "bowtie" ]
