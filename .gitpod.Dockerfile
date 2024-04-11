FROM gitpod/workspace-python-3.12:latest

USER gitpod

RUN python3.12 -m pip install -r https://raw.githubusercontent.com/bowtie-json-schema/bowtie/main/requirements.txt && pyenv rehash
