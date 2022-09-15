# The official clojure images seem to give:
#    no image found in manifest list for architecture arm64, variant "v8", OS linux
FROM alpine AS builder
RUN apk --update add leiningen
WORKDIR /usr/src/app
COPY project.clj /usr/src/app/
RUN lein deps
COPY . .
RUN mv "$(lein uberjar | sed -n 's/^Created \(.*standalone\.jar\)/\1/p')" app-standalone.jar

FROM alpine
WORKDIR /usr/src/app
RUN apk --update add openjdk17-jre
COPY --from=builder /usr/src/app/app-standalone.jar .
CMD ["java", "-jar", "app-standalone.jar"]
