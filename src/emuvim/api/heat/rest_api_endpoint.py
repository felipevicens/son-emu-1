

import logging
import compute
import network
import yaml_reader

class RestApiEndpoint(object):

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port

    def connectDatacenter(self, dc):
        compute.dcs[dc.label] = dc
        logging.info("Connected DC(%s) to API endpoint %s(%s:%d)" % (dc.label, self.__class__.__name__, self.ip, self.port))


    def connectDCNetwork(self, DCnetwork):

        network.net = DCnetwork
        # monitor.net = DCnetwork # TODO add the monitor part

        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self):
        # TODO Start a thread for the REST API listener
        self.read_heat_file()

    def read_heat_file(self):
        inputFile = open('yamlTest1', 'r')
        inp = inputFile.read()
        reader = yaml_reader.YAMLReader()
        reader.parse_input(inp)
