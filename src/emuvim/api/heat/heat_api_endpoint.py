import time
import logging
import compute
import network
import heat_parser
from resources import Stack
import threading
from flask import Flask
from flask_restful import Api
from receive_configuration import ReceiveConfiguration

class HeatApiEndpoint(object):


    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port
        self.heat_net = network.HeatNet()
        self.heat_compute = compute.HeatCompute()

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

        self.api.add_resource(ReceiveConfiguration, "/heatapi/receive/<identifyer>")

    def connectDatacenter(self, dc):
        self.heat_compute.dc = dc
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
        self.read_heat_file()
        self.app.run(self.ip, self.port, debug=True, use_reloader=False)
        # self.deploy_simulation() #TODO start a simulation

    def read_heat_file(self):
        stack = Stack()
        inputFile = open('yamlTest2', 'r')
        inp = inputFile.read()
        reader = heat_parser.HeatParser()
        reader.parse_input(inp, stack)
        logging.debug(stack)
        self.heat_compute.add_stack(stack)
        self.heat_compute.deploy_stack(stack.id)

    def deploy_simulation(self):
        for server in compute.server_list:
            server.start_compute("datacenter1")

if __name__ == "__main__":
    ha = HeatApiEndpoint("localhost", 5000)
    ha.start()
    while True:
        time.sleep(0.2)
