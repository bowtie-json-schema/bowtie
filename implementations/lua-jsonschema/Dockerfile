FROM alpine:3.22

ARG LUAROCKS_VERSION=3.12.2

RUN apk add --no-cache luajit luajit-dev pcre-dev gcc libc-dev curl git make cmake && \
    wget "https://luarocks.org/releases/luarocks-${LUAROCKS_VERSION}.tar.gz" && \
    tar -xf luarocks-${LUAROCKS_VERSION}.tar.gz && rm luarocks-${LUAROCKS_VERSION}.tar.gz && \
    cd luarocks-${LUAROCKS_VERSION} && ./configure && make && make install && \
    cd .. && rm -r luarocks-${LUAROCKS_VERSION} && \
    sed -i '/WGET/d' /usr/local/share/lua/5.1/luarocks/fs/tools.lua && \
    luarocks install jsonschema && \
    apk del luajit-dev gcc git libc-dev curl make cmake

WORKDIR /usr/src/myapp
COPY json.lua bowtie_jsonschema.lua ./
CMD ["luajit", "bowtie_jsonschema.lua"]
