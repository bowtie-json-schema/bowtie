FROM alpine:3.24.1

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

# java-specific setup
RUN apk add openjdk21 maven
RUN cd $(jsu-compile --runtime)/java && mvn install
RUN echo -n "export CLASSPATH=/usr/src/myapp/work:" > .env
RUN find / -type f -name '*.jar' -print | \
    egrep "json-model|getopt|gson|jakarta|johnzon|jackson" | \
    grep -v "maven" | \
    tr '\012' ':' >> .env
RUN echo >> .env

COPY bowtie_jsu_compile.py .
CMD ["python3", "./bowtie_jsu_compile.py", "Java"]
