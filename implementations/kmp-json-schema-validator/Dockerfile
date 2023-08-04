FROM gradle:8.2.1-jdk11
WORKDIR /opt/app
COPY settings.gradle.kts .
COPY build.gradle.kts .
RUN gradle dependencies > /dev/null
COPY src/ src/
RUN gradle --parallel install
CMD ["./build/install/kmp-json-schema-validator/bin/kmp-json-schema-validator"]