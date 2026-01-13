FROM alpine:3.22
WORKDIR /usr/src/myapp

RUN apk add --no-cache \
    build-base \
    lua5.1-dev \
    luarocks5.1 \
    pcre-dev \
    luajit \
 && luarocks-5.1 install jsonschema \
 && apk del --no-cache build-base
COPY json.lua bowtie_jsonschema.lua ./

CMD ["luajit", "bowtie_jsonschema.lua"]
