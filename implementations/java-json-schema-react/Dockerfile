#Build Jar
FROM gradle:9.6.1-jdk21-alpine AS build
WORKDIR /home/gradle/validator
COPY --chown=gradle build.gradle /home/gradle/validator/build.gradle
COPY bowtie/JsonSchemaValidator.java /home/gradle/validator/bowtie/JsonSchemaValidator.java
RUN gradle jar --no-daemon

# Shrink JRE
FROM eclipse-temurin:25-jdk-alpine as jre_builder
WORKDIR /app
COPY --from=build /home/gradle/validator/build/libs/*.jar /app/
RUN jlink \
    --add-modules java.base,java.net.http \
    --strip-debug \
    --no-man-pages \
    --no-header-files \
    --output /app/custom-jre

# final image
FROM alpine:latest
WORKDIR /app
COPY --from=jre_builder /app/custom-jre/ /app/custom-jre
COPY --from=build /home/gradle/validator/build/libs/*.jar /app/
ENV JAVA_HOME=/app/custom-jre
ENV PATH="$JAVA_HOME/bin:$PATH"
ENTRYPOINT ["java", "-jar", "/app/json-schema.jar"]
