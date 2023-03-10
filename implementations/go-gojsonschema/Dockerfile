FROM golang:1.20-buster AS builder

WORKDIR /usr/src/app

COPY go.mod go.sum ./
RUN go mod download && go mod verify

COPY . .

RUN go build -v -o bowtie-gojsonschema

FROM gcr.io/distroless/base-debian10
COPY --from=builder /usr/src/app/bowtie-gojsonschema /usr/local/bin/
CMD ["bowtie-gojsonschema"]
