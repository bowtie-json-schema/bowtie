FROM gradle:8.3.0-jdk11
WORKDIR /app
COPY . .
RUN gradle installDist --no-daemon
RUN chmod +x ./build/install/bowtie/bin/openapiprocessor
CMD ["/app/build/install/bowtie/bin/openapiprocessor"]
