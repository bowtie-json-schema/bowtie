FROM alpine:3.24.0

# NOTE python images do not seem to have google-re2 python wrapper available
# without recompiling from sources, whereas the base alpine image has it,
# so start from alpine.

RUN mkdir -p /usr/src/myapp
WORKDIR /usr/src/myapp

# allow to install from package (not set) or build from sources (branch or commit)
ARG JMC
ARG JSU

RUN apk add git py3-pip py3-re2 py3-dotenv icu-data-full

# force install, otherwise it would require a virtual environment
RUN pip install --break-system-packages jsonschema-specifications
RUN if [ "$JMC" ] ; then jmc="git+https://github.com/clairey-zx81/json-model@$JMC" ; fi ; \
    pip install --break-system-packages "${jmc:-json_model_compiler}"
RUN if [ "$JSU" ] ; then jsu="git+https://github.com/zx80/json-schema-utils@$JSU" ; fi ; \
    pip install --break-system-packages "${jsu:-json_schema_utils}"

# perl-specific setup
RUN apk add perl perl-json perl-json-maybexs
RUN echo -n "export PERLLIB=/usr/src/myapp/work:" > .env
RUN echo $(jsu-compile --runtime)/pl/lib >> .env

# install more perl dependencies
RUN apk add build-base perl-dev perl-app-cpanminus jq make ; \
    cd $(jsu-compile --runtime)/pl && \
    perl Makefile.PL && \
    make install && \
    jq -r ".prereqs.runtime.requires|keys[]" MYMETA.json | grep -v "^perl$" | xargs cpanm --notest && \
    apk del build-base perl-dev perl-app-cpanminus jq make

COPY bowtie_jsu_compile.py .
CMD ["python3", "./bowtie_jsu_compile.py", "Perl", "--regex-engine", "re"]
