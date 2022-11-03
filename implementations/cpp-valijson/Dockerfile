FROM alpine AS builder

RUN apk add --no-cache cmake g++ git make rapidjson-dev

WORKDIR /tmp
RUN git clone --recurse-submodules --depth=1 https://github.com/tristanpenman/valijson.git
RUN mkdir valijson/build && cd valijson/build && cmake .. && cmake --install .

WORKDIR /usr/src/myapp
COPY . .

RUN g++ -static -std=c++17 -o bowtie-valijson bowtie_valijson.cpp

FROM alpine
COPY --from=builder /usr/src/myapp/bowtie-valijson /usr/local/bin

CMD ["bowtie-valijson"]
