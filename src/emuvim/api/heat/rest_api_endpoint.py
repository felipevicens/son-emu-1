

import logging
import compute
import network
import heat_parser
from resources import Stack

class RestApiEndpoint(object):

    def __init__(self, listen_ip, port):
        self.ip = listen_ip
        self.port = port
        self.heat_net = network.HeatNet()
        self.heat_compute = compute.HeatCompute()

    def connectDatacenter(self, dc):
        self.heat_compute.dcs[dc.label] = dc
        logging.info("Connected DC(%s) to API endpoint %s(%s:%d)" % (dc.label, self.__class__.__name__, self.ip, self.port))


    def connectDCNetwork(self, DCnetwork):
        self.heat_net.net = DCnetwork
        # monitor.net = DCnetwork # TODO add the monitor part

        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self):
        # TODO Start a thread for the REST API listener
        self.read_heat_file()
        #self.deploy_simulation() #TODO start a simulation

    def read_heat_file(self):
        stack = Stack()
        self.heat_compute.add_stack(stack)
        inputFile = open('yamlTest2', 'r')
        inp = inputFile.read()
        reader = heat_parser.HeatParser()
        reader.parse_input(inp, stack)

    def deploy_simulation(self):
        for server in compute.server_list:
            server.start_compute("datacenter1")