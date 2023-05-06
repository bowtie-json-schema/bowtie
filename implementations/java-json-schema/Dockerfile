FROM gradle:jdk17-alpine
COPY BowtieJsonSchema.java /opt/app/BowtieJsonSchema.java
COPY build.gradle /opt/app/build.gradle
WORKDIR /opt/app
RUN gradle jar
CMD ["java", "-jar", "build/libs/harness.jar"]
