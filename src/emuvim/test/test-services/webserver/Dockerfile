FROM ubuntu:xenial
MAINTAINER joka@uni-paderborn.de

RUN	apt-get update && apt-get install -y \
	net-tools \
	iproute \
	inetutils-ping


RUN apt-get install -y nginx
ADD start.sh start.sh
RUN chmod +x start.sh
ENV SON_EMU_CMD "./start.sh"

CMD /bin/bash
