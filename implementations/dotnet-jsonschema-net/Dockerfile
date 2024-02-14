FROM --platform=$BUILDPLATFORM mcr.microsoft.com/dotnet/sdk:8.0.101 AS build
WORKDIR /source

COPY *.csproj .
RUN dotnet restore

COPY . .
RUN dotnet publish -c Release -o /app --no-restore

FROM mcr.microsoft.com/dotnet/runtime:8.0-alpine
WORKDIR /app
COPY --from=build /app .
ENTRYPOINT ["dotnet", "bowtie_json_everything.dll"]
