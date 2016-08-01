import time
import logging
import compute
import network
import yaml_reader
import threading
from flask import Flask
from flask_restful import Api
from receive_configuration import ReceiveConfiguration

class HeatApiEndpoint(object):


    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.api.add_resource(ReceiveConfiguration, "/heatapi/receive/<identifyer>")

    def connectDatacenter(self, dc):
        compute.dcs[dc.label] = dc
        logging.info \
            ("Connected DC(%s) to API endpoint %s(%s:%d)" % (dc.label, self.__class__.__name__, self.ip, self.port))

    def connectDCNetwork(self, DCnetwork):

        network.net = DCnetwork
        # monitor.net = DCnetwork # TODO add the monitor part

        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self):


        thread = threading.Thread(target=self._start_flask, args=())
        thread.daemon = True
        thread.start()
        logging.info("Started API endpoint @ http://%s:%d" % (self.ip, self.port))

    def _start_flask(self):
        self.app.run(self.ip, self.port, debug=True, use_reloader=False)


        # TODO Start a thread for the REST API listener
        self.read_heat_file()
        # self.deploy_simulation() #TODO start a simulation

    def read_heat_file(self):
        inputFile = open('yamlTest2', 'r')
        inp = inputFile.read()
        reader = yaml_reader.YAMLReader()
        reader.parse_input(inp)

    def deploy_simulation(self):
        for server in compute.server_list:
            server.start_compute("datacenter1")

if __name__ == "__main__":
    ha = HeatApiEndpoint("localhost", 5000)
    ha.start()
    while True:
        time.sleep(0.2)
