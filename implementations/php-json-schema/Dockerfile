FROM php:8.2-fpm-alpine

WORKDIR /var/www/html

COPY bowtieJsonSchema.php .
COPY nginx.conf /etc/nginx/conf.d/default.conf

RUN apk update && apk add --no-cache nginx

CMD nginx && php-fpm
