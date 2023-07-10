FROM gradle:8.2.0-jdk17
COPY BowtieJsonSchemaValidator.java /opt/app/BowtieJsonSchemaValidator.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN gradle jar --no-daemon
CMD ["java", "-jar", "build/libs/harness.jar"]
