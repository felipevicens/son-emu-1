import logging
import threading
import time

from flask import Flask
from flask_restful import Api,Resource
from openstack_dummies import *
import compute
import heat_parser
import network

from resources import Stack


class OpenstackApiEndpoint():

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port
        self.compute = compute.OpenstackCompute()
        self.openstack_endpoints = dict()
        self.openstack_endpoints['keystone'] = list()
        self.openstack_endpoints['nova'] = list()
        self.openstack_endpoints['neutron'] = list()
        self.openstack_endpoints['heat'] = list()
        self.rest_threads = list()
        self.openstack_networks = list()


    def connect_datacenter(self, dc):
        self.compute.dc = dc

        self.openstack_endpoints['keystone'].append(KeystoneDummyApi(self.ip, self.port))
        self.openstack_endpoints['neutron'].append(NeutronDummyApi(self.ip, self.port + 4696))
        self.openstack_endpoints['nova'].append(NovaDummyApi(self.ip, self.port + 3774))
        self.openstack_endpoints['heat'].append(HeatDummyApi(self.ip, self.port + 3004))
        logging.info \
            ("Connected DC(%s) to API endpoint %s(%s:%d)" % (dc.label, self.__class__.__name__, self.ip, self.port))

    def connect_dc_network(self, dc_network):
        tmp_network = network.OpenstackNet(dc_network)
        self.openstack_networks.append(tmp_network)
        # monitor.net = DCnetwork # TODO add the monitor part

        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self):
        for component in self.openstack_endpoints.values():
            for endpoint in component:
                endpoint.compute = self.compute
                thread = threading.Thread(target=endpoint._start_flask, args=())
                thread.daemon = True
                thread.name = endpoint.__class__
                thread.start()
        #self.deploy_simulation() #TODO start a simulation

    def read_heat_file(self):
        stack = Stack()
        inputFile = open('yamlTest2', 'r')
        inp = inputFile.read()
        reader = heat_parser.HeatParser()
        reader.parse_input(inp, stack, self.compute.dc.label)
        logging.debug(stack)
        self.compute.add_stack(stack)
        self.compute.deploy_stack(stack.id)

    def deploy_simulation(self):
        for server in compute.server_list:
            server.start_compute("datacenter1")

if __name__ == "__main__":
    ha = OpenstackApiEndpoint("localhost", 5000)
    ha.start()
    while True:
        time.sleep(0.5)
