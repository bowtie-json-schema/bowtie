FROM alpine:3.24.1 AS builder

RUN apk add --no-cache \
    build-base \
    perl-dev \
    perl-app-cpanminus \
 && cpanm --notest JSON::Schema::Modern

FROM alpine:3.24.1
WORKDIR /harness

RUN apk add --no-cache \
    lsb-release-minimal \
    perl
COPY --from=builder /usr/local/lib/perl5/site_perl /usr/local/lib/perl5/site_perl
COPY --from=builder /usr/local/share/perl5/site_perl /usr/local/share/perl5/site_perl
COPY bowtie_runner.pl ./

CMD ["./bowtie_runner.pl"]
