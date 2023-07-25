FROM php:8.2-fpm-alpine

RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer

WORKDIR /app

COPY bowtieJsonSchema.php ./
COPY composer.json ./

RUN composer install --no-scripts --no-autoloader
RUN composer dump-autoload --optimize

CMD ["php", "bowtieJsonSchema.php"]
