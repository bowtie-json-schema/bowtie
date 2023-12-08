FROM sbtscala/scala-sbt:eclipse-temurin-17.0.4_1.7.2_2.13.10 AS builder

RUN git clone https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator /opt/mjs
WORKDIR /opt/mjs
RUN git checkout v0.1.0
RUN sbt assembly

WORKDIR /opt/harness
COPY Harness.scala /opt/harness
COPY build.sbt /opt/harness
COPY project /opt/harness/project
RUN mkdir lib && cp /opt/mjs/target/scala-*/jschemavalidator.jar /opt/harness/lib/mjs.jar
RUN sbt assembly

FROM bellsoft/liberica-openjdk-alpine:17
COPY --from=builder /opt/harness/target/scala-*/validator.jar /opt/app/validator.jar
CMD ["java", "-Xss8m", "-Xmx16g", "-jar", "/opt/app/validator.jar"]

