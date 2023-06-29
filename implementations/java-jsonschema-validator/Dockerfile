FROM gradle:8.1.1-jdk17
COPY bowtieJsonSchemaValidator.java /opt/app/bowtieJsonSchemaValidator.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN gradle jar --no-daemon
CMD ["java", "-jar", "build/libs/harness.jar"]