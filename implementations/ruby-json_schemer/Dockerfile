FROM ruby:3-alpine as builder

# unf_ext wants libc++ to compile itself
RUN apk add --no-cache g++ make
COPY Gemfile* .
RUN bundle install

FROM ruby:3-alpine
WORKDIR /usr/src/app
COPY --from=builder /usr/local/bundle/ /usr/local/bundle/
COPY . .
CMD ["ruby", "bowtie_json_schemer.rb"]
