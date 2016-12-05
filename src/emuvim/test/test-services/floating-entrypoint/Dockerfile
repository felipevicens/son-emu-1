FROM      ubuntu:xenial
MAINTAINER joka@uni-paderborn.de 

RUN	apt-get update --fix-missing && apt-get install -y \
	net-tools \
	iproute \
	inetutils-ping

# install OpenvSwitch 
RUN apt-get install -y iptables 


ADD start_fw.sh start.sh
RUN chmod +x start.sh


# set entry point for emulator gatekeeper
ENV SON_EMU_CMD "./start.sh"

CMD /bin/bash
