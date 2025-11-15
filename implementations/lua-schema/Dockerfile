FROM alpine:3.22
WORKDIR /harness

RUN apk add --no-cache \
    lua5.4 \
    lua5.4-lpeg \
    lua5.4-rex-pcre2 \
    luarocks5.4 \
 && luarocks-5.4 install dkjson \
 && luarocks-5.4 install --dev lua-schema
COPY bowtie_schema.lua ./

CMD ["lua5.4", "bowtie_schema.lua"]
