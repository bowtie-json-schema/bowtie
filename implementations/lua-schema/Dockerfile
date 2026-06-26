FROM alpine:3.24.1 AS builder

RUN apk add --no-cache \
    lua5.4 \
    lua5.4-lpeg \
    luarocks5.4 \
 && luarocks-5.4 install lua-schema

FROM alpine:3.24.1
WORKDIR /harness

RUN echo "@testing https://dl-cdn.alpinelinux.org/alpine/edge/testing" >> /etc/apk/repositories
RUN apk add --no-cache \
    lsb-release-minimal \
    lua5.5 \
    lua5.5-dkjson@testing \
    lua5.5-lpeg \
    lua5.5-rex-pcre2
COPY --from=builder /usr/local/share/lua/5.4 /usr/local/share/lua/5.5
COPY bowtie_schema.lua ./

CMD ["lua5.5", "bowtie_schema.lua"]
