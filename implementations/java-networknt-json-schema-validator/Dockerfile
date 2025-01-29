FROM gradle:8.12.1-jdk17 AS builder
COPY BowtieJsonSchemaValidator.java /opt/app/BowtieJsonSchemaValidator.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN gradle jar --no-daemon

FROM bellsoft/liberica-openjdk-alpine:23
COPY --from=builder /opt/app/build/libs /opt/app
CMD ["java", "-jar", "/opt/app/harness.jar"]
