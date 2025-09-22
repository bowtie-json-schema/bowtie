FROM gradle:9.1-jdk17 AS builder
WORKDIR /opt/app
COPY . .
RUN gradle installDist --no-daemon
RUN chmod +x ./build/install/bowtie/bin/openapiprocessor

FROM bellsoft/liberica-openjdk-alpine:25
COPY --from=builder /opt/app/build /opt/app/build
CMD ["/opt/app/build/install/bowtie/bin/openapiprocessor"]
