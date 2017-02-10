from flask import Flask
from flask_restful import Api, Resource
import logging


class BaseOpenstackDummy(Resource):
    """
    This class is the base class for all openstack entrypoints of son-emu.
    """

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port
        self.compute = None
        self.manage = None

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)
