FROM gradle:9.1-jdk17 AS builder
COPY BowtieSjf4jValidator.java /opt/app/BowtieSjf4jValidator.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN gradle jar --no-daemon

FROM bellsoft/liberica-openjdk-alpine:25
COPY --from=builder /opt/app/build/libs /opt/app
CMD ["java", "-jar", "/opt/app/harness.jar"]
