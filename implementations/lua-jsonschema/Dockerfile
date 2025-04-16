FROM alpine:3.21
RUN apk add --no-cache luajit luajit-dev pcre-dev gcc libc-dev curl git make cmake && \
    wget 'https://luarocks.org/releases/luarocks-3.9.2.tar.gz' && \
    tar -xf luarocks-3.9.2.tar.gz && rm luarocks-3.9.2.tar.gz && \
    cd luarocks-3.9.2 && ./configure && make && make install && \
    cd .. && rm -r luarocks-3.9.2 && \
    sed -i '/WGET/d' /usr/local/share/lua/5.1/luarocks/fs/tools.lua && \
    luarocks install jsonschema && \
    apk del luajit-dev gcc git libc-dev curl make cmake
WORKDIR /usr/src/myapp
COPY json.lua bowtie_jsonschema.lua ./
CMD ["luajit", "bowtie_jsonschema.lua"]
