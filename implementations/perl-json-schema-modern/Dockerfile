FROM alpine:3.22
WORKDIR /harness

RUN apk add --no-cache \
    build-base \
    perl-dev \
    perl-app-cpanminus \
 && cpanm --notest JSON::Schema::Modern \
 && apk del --no-cache build-base
COPY bowtie_runner.pl ./

CMD ["./bowtie_runner.pl"]
