FROM elixir:1.18-otp-27-alpine AS builder

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
RUN mix compile && mix escript.build

FROM erlang:27-alpine

RUN apk add --no-cache openssl ncurses-libs libstdc++
COPY --from=builder /opt/app/bowtie_jsv /opt/app/bowtie_jsv

RUN mkdir -p /var/log/jsv

ENTRYPOINT [ "/opt/app/bowtie_jsv" ]
