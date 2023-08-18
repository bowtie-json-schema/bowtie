FROM gradle:8.3.0-jdk17
COPY BowtieJsonSchema.java /opt/app/BowtieJsonSchema.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN gradle jar --no-daemon
CMD ["java", "-jar", "build/libs/harness.jar"]
