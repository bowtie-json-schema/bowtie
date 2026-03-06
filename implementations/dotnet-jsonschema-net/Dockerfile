FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:10.0 AS build
ARG TARGETARCH

WORKDIR /source

COPY *.csproj .
RUN dotnet restore -a ${TARGETARCH}

COPY . .
RUN dotnet publish -a ${TARGETARCH} --no-restore -c Release -o /app

FROM mcr.microsoft.com/dotnet/runtime:10.0
WORKDIR /app
COPY --from=build /app .
ENTRYPOINT ["dotnet", "bowtie_json_everything.dll"]
