# The official clojure images seem to give:
#    no image found in manifest list for architecture arm64, variant "v8", OS linux
FROM alpine AS builder
RUN apk add --no-cache leiningen
WORKDIR /usr/src/app
COPY project.clj /usr/src/app/
RUN lein deps
COPY . .
RUN mv "$(lein uberjar | sed -n 's/^Created \(.*standalone\.jar\)/\1/p')" app-standalone.jar

FROM bellsoft/liberica-openjdk-alpine:24
WORKDIR /usr/src/app
COPY --from=builder /usr/src/app/app-standalone.jar .
CMD ["java", "-jar", "app-standalone.jar"]
