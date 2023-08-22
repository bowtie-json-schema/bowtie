#Docker container for a simple java setup to communicate with Bowtie.

FROM gradle:8.3.0-jdk11

COPY Harness.java /usr/src
COPY build.gradle /usr/src
COPY mjs.jar /usr/src

WORKDIR /usr/src/

# We need to define the command to launch when we are going to run the image.
# We use the keyword 'CMD' to do that.
# The following command will execute "java".
#ENV JAVA_OPTS="-Xms2550M -Xmx50M"
RUN gradle jar --no-daemon
CMD [ "java", "-Xss8m", "-jar", "build/libs/validator.jar"]
