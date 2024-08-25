FROM gradle:8.10.0-jdk17 AS builder
ARG IMPLEMENTATION_VERSION
COPY BowtieJsonSchema.java /opt/app/BowtieJsonSchema.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN if [ -n "$IMPLEMENTATION_VERSION" ]; then \
      sed -i "/group: 'dev.harrel',/,/version:/ s/version: '[^']*'/version: '$IMPLEMENTATION_VERSION'/" build.gradle; \
    fi
RUN gradle jar --no-daemon

FROM bellsoft/liberica-openjdk-alpine:22
COPY --from=builder /opt/app/build/libs /opt/app
CMD ["java", "-jar", "/opt/app/harness.jar"]
