FROM composer:2.10.2 AS builder

WORKDIR /usr/src/json-schema

COPY ./src ./src
COPY ./bootstrap.php .
COPY composer.* .
RUN composer install --no-dev --no-scripts --no-interaction --prefer-dist --optimize-autoloader
RUN composer dump-autoload --no-dev --optimize --classmap-authoritative

FROM php:8.5.7-cli-alpine3.22

WORKDIR /usr/src/json-schema

RUN apk add --no-cache lsb-release-minimal
COPY ./src ./src
COPY ./bootstrap.php .
COPY composer.* .
COPY --from=builder /usr/src/json-schema/vendor /usr/src/json-schema/vendor

CMD ["php", "bootstrap.php"]
