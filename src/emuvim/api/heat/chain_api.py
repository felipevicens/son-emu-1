from flask import Flask
from flask_restful import Api, Resource
from flask import Response
import logging
import json


class ChainApi(Resource):
    def __init__(self, inc_ip, inc_port, manage):
        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.ip = inc_ip
        self.port = inc_port
        self.manage = manage
        self.api.add_resource(ChainVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnf, "/v1/chain/<src_vnf>/<dst_vnf>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnfInterfaces, "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(LoadBalancer, "/v1/lb/<name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(BalanceHost, "/v1/lb/<name>",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("ChainDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class ChainVersionsList(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        # at least let it look like an open stack function
        try:
            resp = """[
                {
                    "versions": [
                        {
                            "id": "v1",
                            "links": [
                                {
                                    "href": "http://%s:%d/v1/",
                                    "rel": "self"
                                }
                            ],
                            "status": "CURRENT",
                            "version": "1",
                            "min_version": "1",
                            "updated": "2013-07-23T11:33:21Z"
                        }
                    ]
                }
            """ % (self.api.ip, self.api.port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class ChainVnf(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, src_vnf, dst_vnf):
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")

        try:
            # check if which interface to chain on
            dst_intfs = None
            src_intfs = None

            for intfs in self.api.manage.net[src_vnf].intfs.values():
                for dintfs in self.api.manage.net[dst_vnf].intfs.values():
                    # if both are in the same network they can be chained
                    if intfs.params[intfs.name] == dintfs.params[dintfs.name]:
                        src_intfs = intfs.name
                        dst_intfs = dintfs.name

            cookie = self.api.manage.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                          vnf_dst_interface=dst_intfs, bidirectional=True)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

    def delete(self, src_vnf, dst_vnf):
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")

        try:
            # check if which interface to chain on
            dst_intfs = None
            src_intfs = None

            for intfs in self.api.manage.net[src_vnf].intfs.values():
                for dintfs in self.api.manage.net[dst_vnf].intfs.values():
                    # if both are in the same network they can be chained
                    if intfs.params[intfs.name] == dintfs.params[dintfs.name]:
                        src_intfs = intfs.name
                        dst_intfs = dintfs.name

            cookie = self.api.manage.network_action_stop(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                          vnf_dst_interface=dst_intfs, bidirectional=True)

            return Response(json.dumps(cookie), status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain", status=500, mimetype="application/json")


class ChainVnfInterfaces(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            cookie = self.api.manage.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                          vnf_dst_interface=dst_intfs, bidirectional=True)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

    def delete(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            cookie = self.api.manage.network_action_stop(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                vnf_dst_interface=dst_intfs, bidirectional=True)
            return Response(json.dumps(cookie), status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain", status=500, mimetype="application/json")


class LoadBalancer(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, name):
        pass


class BalanceHost(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, name):
        pass
