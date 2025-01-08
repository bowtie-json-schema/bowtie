FROM elixir:1.18-alpine

WORKDIR /app

RUN mix local.hex --force && mix local.rebar --force

COPY mix.exs mix.exs

RUN mix deps.get && mix deps.compile

COPY lib lib

RUN mix compile && mix escript.build

ENTRYPOINT [ "./bowtie_jsv" ]