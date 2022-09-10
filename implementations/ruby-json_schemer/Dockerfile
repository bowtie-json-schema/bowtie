FROM ruby:3-slim
WORKDIR /usr/src/app
COPY . .
RUN bundle install
CMD ["ruby", "bowtie_json_schemer.rb"]
