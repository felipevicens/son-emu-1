# -*- coding: utf-8 -*-

import logging

from flask import Flask
from flask_restful import Api,Resource

logging.basicConfig(level=logging.INFO)

class BaseOpenstackDummy(Resource):
    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port
        self.compute = None
        self.os_net = None

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)


    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

    #TODO: this method should be abstract!
    def set_os_net(self, net):
        self.os_net = net
