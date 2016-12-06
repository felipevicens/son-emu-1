FROM ubuntu:xenial
MAINTAINER joka@uni-paderborn.de

RUN	apt-get update && apt-get install -y \
	net-tools \
	iproute \
	inetutils-ping


RUN apt-get install -y nginx php-fpm
ADD nginx.conf /etc/nginx/nginx.conf
ADD default /etc/nginx/sites-available/default
RUN rm -f /var/www/html/*
ADD index.php /var/www/html/index.php
RUN chmod 755 /var/www/html/index.php
ADD start.sh start.sh
RUN chmod +x start.sh
ENV SON_EMU_CMD "./start.sh"

CMD /bin/bash
