FROM gradle:8.2.1-jdk11
WORKDIR /app
COPY . .
RUN gradle installDist --no-daemon
RUN chmod +x ./build/install/bowtie/bin/openapiprocessor
CMD ["/app/build/install/bowtie/bin/openapiprocessor"]
