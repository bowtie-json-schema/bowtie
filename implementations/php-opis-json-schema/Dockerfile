FROM composer:2.8 AS builder

WORKDIR /usr/src/myapp

COPY composer.* .
RUN composer install --no-dev --no-scripts --no-interaction --prefer-dist --optimize-autoloader
COPY bowtieJsonSchema.php .
RUN composer dump-autoload --no-dev --optimize --classmap-authoritative

FROM php:8.4.7-fpm-alpine

WORKDIR /usr/src/myapp

COPY bowtieJsonSchema.php .
COPY --from=builder /usr/src/myapp/vendor /usr/src/myapp/vendor

CMD ["php", "bowtieJsonSchema.php"]
