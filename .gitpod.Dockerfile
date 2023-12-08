FROM gitpod/workspace-full:2023-11-24-15-04-57
ENV SHELL=/usr/bin/zsh
RUN pyenv install 3.11 && pyenv global 3.11
