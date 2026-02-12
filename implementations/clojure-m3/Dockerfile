FROM alpine AS builder
RUN apk add --no-cache leiningen
WORKDIR /usr/src/app
COPY project.clj /usr/src/app/
RUN lein deps
COPY . .
RUN mv "$(lein uberjar | sed -n 's/^Created \(.*standalone\.jar\)/\1/p')" app-standalone.jar

FROM bellsoft/liberica-openjdk-alpine:25
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/app-standalone.jar .
CMD ["java", "-Dpolyglot.engine.WarnInterpreterOnly=false", "-Dorg.slf4j.simpleLogger.defaultLogLevel=off", "-jar", "app-standalone.jar"]
