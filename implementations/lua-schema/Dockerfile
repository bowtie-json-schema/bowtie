FROM alpine:3.24.1 AS builder

RUN apk add --no-cache \
    lua5.4 \
    lua5.4-lpeg \
    luarocks5.4 \
 && luarocks-5.4 install dkjson \
 && luarocks-5.4 install lua-schema

FROM alpine:3.24.1
WORKDIR /harness

RUN apk add --no-cache \
    lsb-release-minimal \
    lua5.4 \
    lua5.4-lpeg \
    lua5.4-rex-pcre2
COPY --from=builder /usr/local/share/lua /usr/local/share/lua
COPY bowtie_schema.lua ./

CMD ["lua5.4", "bowtie_schema.lua"]
