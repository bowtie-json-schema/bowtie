FROM gradle:8.14-jdk17 AS builder
WORKDIR /opt/app
COPY . .
RUN gradle installDist --no-daemon
RUN chmod +x ./build/install/bowtie/bin/openapiprocessor

FROM bellsoft/liberica-openjdk-alpine:24
COPY --from=builder /opt/app/build /opt/app/build
CMD ["/opt/app/build/install/bowtie/bin/openapiprocessor"]
