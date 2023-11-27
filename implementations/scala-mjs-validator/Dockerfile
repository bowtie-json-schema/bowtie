FROM sbtscala/scala-sbt:eclipse-temurin-17.0.4_1.7.1_3.2.0 AS sbt
RUN git clone https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator.git /opt/app
WORKDIR /opt/app
RUN sbt assembly

FROM gradle:8.4.0-jdk17 AS builder
WORKDIR /opt/app
COPY Harness.java .
COPY build.gradle .
COPY --from=sbt /opt/app/target/scala-*/jschemavalidator.jar mjs.jar
RUN gradle jar --no-daemon

FROM bellsoft/liberica-openjdk-alpine:21
COPY --from=builder /opt/app/build/libs /opt/app
CMD ["java", "-jar", "/opt/app/harness.jar"]
