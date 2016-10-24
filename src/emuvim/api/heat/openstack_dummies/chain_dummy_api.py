# -*- coding: utf-8 -*-

from flask_restful import Resource
from flask import Response, request
from flask import jsonify
import logging
import json
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy


class ChainDummyApi(BaseOpenstackDummy):
    def __init__(self, inc_ip, inc_port, compute):
        super(ChainDummyApi, self).__init__(inc_ip, inc_port)
        self.compute = compute

        self.api.add_resource(ChainVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(ChainVnf, "/v1/chain/<src_vnf>/<dst_vnf>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnfInterfaces, "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(UnchainVnf, "/v1/unchain/<src_vnf>/<dst_vnf>",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("ChainDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut doen") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

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

    def get(self, src_vnf, dst_vnf):
        # check if both VNFs exist
        if src_vnf not in self.api.compute.dc.net or dst_vnf not in self.api.compute.dc.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")

        try:
            # check if which interface to chain on
            dst_intfs = None
            src_intfs = None

            for intfs in self.api.compute.dc.net[src_vnf].intfs.values():
                for dintfs in self.api.compute.dc.net[dst_vnf].intfs.values():
                    # if both are in the same network they can be chained
                    if intfs.params[intfs.name] == dintfs.params[dintfs.name]:
                        src_intfs = intfs.name
                        dst_intfs = dintfs.name

            self.api.os_net.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                 vnf_dst_interface=dst_intfs, bidirectional=True)
        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

class ChainVnfInterfaces(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        # check if both VNFs exist
        if src_vnf not in self.api.compute.dc.net or dst_vnf not in self.api.compute.dc.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            self.api.os_net.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                 vnf_dst_interface=dst_intfs, bidirectional=True)
        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

class UnchainVnf(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, src_vnf, dst_vnf):
        # check if both VNFs exist
        if src_vnf not in self.api.compute.dc.net or dst_vnf not in self.api.compute.dc.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            self.api.os_net.network_action_start(src_vnf, dst_vnf, bidirectional=True)
        except Exception as e:
            logging.exception(u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain", status=500, mimetype="application/json")