FROM gitpod/workspace-python-3.13:latest

USER gitpod

RUN python3.13 -m pip install -r https://raw.githubusercontent.com/bowtie-json-schema/bowtie/main/requirements.txt && pyenv rehash
