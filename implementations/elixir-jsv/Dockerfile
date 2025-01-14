FROM elixir:1.18-alpine AS builder

WORKDIR /opt/app

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

FROM alpine:3.21

RUN apk add --no-cache openssl ncurses-libs libstdc++
COPY --from=builder /opt/app/_build/prod/rel/bowtie_jsv /opt/app/bowtie_jsv

ENTRYPOINT [ "/opt/app/bowtie_jsv/bin/bowtie_jsv", "start" ]
