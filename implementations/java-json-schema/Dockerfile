FROM gradle:8.14-jdk17 AS builder
ARG IMPLEMENTATION_VERSION
COPY BowtieJsonSchema.java /opt/app/BowtieJsonSchema.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN gradle jar --no-daemon ${IMPLEMENTATION_VERSION:+-PimplementationVersion=}${IMPLEMENTATION_VERSION}

FROM bellsoft/liberica-openjdk-alpine:24
COPY --from=builder /opt/app/build/libs /opt/app
CMD ["java", "-jar", "/opt/app/harness.jar"]
