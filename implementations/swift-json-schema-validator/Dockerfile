FROM swift:latest AS build
WORKDIR /app
COPY . .
RUN swift build -c release

FROM swift:slim
WORKDIR /app
COPY --from=build /app/.build/release/BowtieJSONSchema .
CMD ["./BowtieJSONSchema"]
