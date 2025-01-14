# Builder image ------------------------------------------------------------- #
FROM elixir:1.18-alpine

WORKDIR /app

# Install Elixir package manager
RUN mix local.hex --force && mix local.rebar --force

# Install and compile dependencies
COPY mix.exs mix.exs
RUN mix deps.get && mix deps.compile

# Copy the actual code
COPY lib lib

# Generate a production release
ENV MIX_ENV=prod
RUN mix compile && mix release --overwrite

# Runner image -------------------------------------------------------------- #
FROM alpine

RUN apk update && apk add --no-cache openssl ncurses-libs libstdc++
COPY --from=0 /app/_build/prod/rel/bowtie_jsv /bowtie_jsv

ENTRYPOINT [ "/bowtie_jsv/bin/bowtie_jsv", "start" ]
