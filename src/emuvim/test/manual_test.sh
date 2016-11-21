#!/bin/bash
source /root/testrc
screen -S emu -X quit
screen -S emu -d -m python ../examples/simple_heat_restapi.py
pid=$!
sleep 10
heat stack-create --template-file test-template-1.yml a
curl -X PUT localhost:4000/v1/chain/dc1_a_firewall1/dc1_a_tcpdump1
curl -X PUT localhost:4000/v1/chain/dc1_a_iperf1/dc1_a_firewall1
neutron net-create test1
neutron subnet-create test1 192.168.5.2/24
neutron port-create test1
#nova --debug boot --image ubuntu:trusty --nic port-id=62a16c27-e257-4e03-8444-209f75c59953 --flavor m1.small test2
screen -x emu
