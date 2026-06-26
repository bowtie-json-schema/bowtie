FROM alpine:3.24.1 AS builder

RUN apk add --no-cache \
    build-base \
    lua5.1-dev \
    luarocks5.1 \
    pcre-dev \
 && luarocks-5.1 install jsonschema

FROM alpine:3.24.1
WORKDIR /usr/src/myapp

RUN apk add --no-cache \
    lsb-release-minimal \
    pcre \
    luajit
COPY --from=builder /usr/local/lib/lua /usr/local/lib/lua
COPY --from=builder /usr/local/share/lua /usr/local/share/lua
COPY json.lua bowtie_jsonschema.lua ./

CMD ["luajit", "bowtie_jsonschema.lua"]
