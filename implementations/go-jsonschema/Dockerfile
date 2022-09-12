FROM golang:1.19-alpine

WORKDIR /usr/src/app

COPY go.mod go.sum ./
RUN go mod download && go mod verify

COPY . .
RUN go build -v -o /usr/local/bin/bowtie-jsonschema ./...

CMD ["bowtie-jsonschema"]
