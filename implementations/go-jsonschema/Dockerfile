FROM --platform=$BUILDPLATFORM golang:1.24-alpine AS builder
ARG TARGETOS
ARG TARGETARCH

WORKDIR /usr/src/app

COPY go.mod go.sum ./
RUN go mod download && go mod verify

COPY . .

RUN GOOS=${TARGETOS} GOARCH=${TARGETARCH} go build -v -o bowtie-jsonschema

FROM gcr.io/distroless/base-debian10
COPY --from=builder /usr/src/app/bowtie-jsonschema /usr/local/bin/
CMD ["bowtie-jsonschema"]
