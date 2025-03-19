FROM sbtscala/scala-sbt:eclipse-temurin-17.0.4_1.7.2_2.13.10 AS builder

WORKDIR /opt/harness
COPY Harness.scala /opt/harness
COPY build.sbt /opt/harness
COPY project /opt/harness/project
RUN sbt assembly

FROM bellsoft/liberica-openjdk-alpine:24
COPY --from=builder /opt/harness/target/scala-*/bowtieRcCirce.jar /opt/app/bowtieRcCirce.jar
CMD ["java", "-jar", "/opt/app/bowtieRcCirce.jar"]
