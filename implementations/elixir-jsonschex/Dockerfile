FROM elixir:1.19.5-otp-28-alpine AS builder
WORKDIR /opt/app
ENV MIX_ENV=prod
RUN mix local.hex --force && mix local.rebar --force
COPY mix.exs mix.exs
RUN mix deps.get --only prod && mix deps.compile
COPY lib lib
RUN mix compile && mix escript.build
FROM erlang:28-alpine
RUN mkdir -p /var/log/jsonschex
COPY --from=builder /opt/app/bowtie_jsonschex /opt/app/bowtie_jsonschex
ENTRYPOINT ["/opt/app/bowtie_jsonschex"]
