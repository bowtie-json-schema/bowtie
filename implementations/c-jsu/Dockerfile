FROM alpine:3.23

# NOTE python images do not seem to have google-re2 python wrapper available
# without recompiling from sources, whereas the base alpine image has it,
# so start from alpine.

RUN mkdir -p /usr/src/myapp
WORKDIR /usr/src/myapp

# allow to install from package (not set) or build from sources (branch or commit)
ARG JMC
ARG JSU

RUN apk add git py3-pip py3-re2 icu-data-full

# force install, otherwise it would require a virtual environment
RUN pip install --break-system-packages jsonschema-specifications
RUN if [ "$JMC" ] ; then jmc="git+https://github.com/clairey-zx81/json-model@$JMC" ; fi ; \
    pip install --break-system-packages "${jmc:-json_model_compiler}"
RUN if [ "$JSU" ] ; then jsu="git+https://github.com/zx80/json-schema-utils@$JSU" ; fi ; \
    pip install --break-system-packages "${jsu:-json_schema_utils}"

# c-specific setup
# NOTE avoid unavailable re2 C wrapper that needs to be installed from sources
RUN apk add gcc musl musl-dev jansson jansson-dev pcre2 pcre2-dev

COPY bowtie_jsu_compile.py .
CMD ["python3", "./bowtie_jsu_compile.py", "C", "--regex-engine", "pcre2"]
