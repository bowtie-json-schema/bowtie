FROM sbtscala/scala-sbt:eclipse-temurin-17.0.4_1.7.1_3.2.0 AS builder
COPY Harness.java /usr/src
COPY build.gradle /usr/src
ENV GRADLE_VERSION=7.2

RUN curl -L https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip -o gradle-${GRADLE_VERSION}-bin.zip
RUN apt-get update -y && \
    apt-get install -y unzip && \
    apt-get clean && \
	unzip "gradle-${GRADLE_VERSION}-bin.zip" -d /opt && \
    rm "gradle-${GRADLE_VERSION}-bin.zip"
ENV GRADLE_HOME=/opt/gradle-${GRADLE_VERSION}
ENV PATH=${GRADLE_HOME}/bin:$PATH

WORKDIR /usr/src/
RUN git clone https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator.git
WORKDIR /usr/src/modernjsonschemavalidator
RUN sbt assembly && \
	mv /usr/src/modernjsonschemavalidator/target/scala-2.13/jschemavalidator-assembly-0.1.0-SNAPSHOT.jar /usr/src/mjs.jar
WORKDIR /usr/src/
RUN gradle jar --no-daemon

FROM bellsoft/liberica-openjdk-alpine:21
COPY --from=builder /usr/src/build/libs /usr/src
CMD ["java", "-jar", "/usr/src/validator.jar"]