FROM mcr.microsoft.com/vscode/devcontainers/python:3.11

# Install Docker CLI
RUN apt-get update \
  && apt-get install -y docker.io
  