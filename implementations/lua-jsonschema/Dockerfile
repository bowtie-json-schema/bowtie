FROM alpine:3.16
RUN apk add --no-cache luajit luajit-dev pcre-dev gcc libc-dev curl make cmake && \
    wget 'https://luarocks.org/releases/luarocks-3.9.1.tar.gz' && \
    tar -xf luarocks-3.9.1.tar.gz && cd luarocks-3.9.1 && \
    ./configure && make && make install
RUN sed -i '/WGET/d' /usr/local/share/lua/5.1/luarocks/fs/tools.lua
RUN luarocks install jsonschema
COPY json.lua bowtie_jsonschema.lua .
CMD ["luajit", "bowtie_jsonschema.lua"]
