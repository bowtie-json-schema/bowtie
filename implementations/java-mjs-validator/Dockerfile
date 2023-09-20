FROM gradle:8.3.0-jdk11
RUN apt-get update && \
    apt-get install -y curl && \
    apt-get clean
RUN curl -L https://github.com/sbt/sbt/releases/download/v1.5.5/sbt-1.5.5.tgz -o sbt-1.5.5.tgz && \
    tar -xzvf sbt-1.5.5.tgz -C /opt && \
    rm sbt-1.5.5.tgz
ENV PATH="/opt/sbt/bin:${PATH}"

COPY Harness.java /usr/src
COPY build.gradle /usr/src
WORKDIR /usr/src/
RUN git clone https://gitlab.lip6.fr/jsonschema/modernjsonschemavalidator.git
WORKDIR /usr/src/modernjsonschemavalidator
RUN sbt assembly
RUN mv /usr/src/modernjsonschemavalidator/target/scala-2.13/jschemavalidator-assembly-0.1.0-SNAPSHOT.jar /usr/src/mjs.jar

WORKDIR /usr/src/
RUN gradle jar --no-daemon
CMD [ "java", "-Xss8m", "-jar", "build/libs/validator.jar"]
