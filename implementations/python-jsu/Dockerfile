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

COPY bowtie_jsu_python.py .
CMD ["python3", "./bowtie_jsu_python.py"]
