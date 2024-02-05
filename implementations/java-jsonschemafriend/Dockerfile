FROM gradle:8.6.0-jdk17 AS builder
WORKDIR /opt/app
COPY BowtieJsonSchemaFriend.java .
COPY build.gradle .
RUN gradle jar --no-daemon

FROM bellsoft/liberica-openjdk-alpine:21
COPY --from=builder /opt/app/build/libs /opt/app
CMD ["java", "-jar", "/opt/app/harness.jar"]
