FROM composer:2.7 AS builder

WORKDIR /usr/src/json-schema

COPY ./src ./src
COPY ./bootstrap.php .
COPY composer.* .
RUN composer install --no-dev --no-scripts --no-interaction --prefer-dist --optimize-autoloader
RUN composer dump-autoload --no-dev --optimize --classmap-authoritative

FROM php:8.3-alpine

WORKDIR /usr/src/json-schema

COPY ./src ./src
COPY ./bootstrap.php .
COPY --from=builder /usr/src/json-schema/vendor /usr/src/json-schema/vendor

CMD ["php", "bootstrap.php"]
