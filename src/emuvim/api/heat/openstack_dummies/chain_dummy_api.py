# -*- coding: utf-8 -*-

from flask_restful import Resource
from flask import Response, request
from flask import jsonify
import logging
import json
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy

compute = None
ip = None
port = None
os_net = None


class ChainDummyApi(BaseOpenstackDummy):
    def __init__(self, inc_ip, inc_port):
        super(ChainDummyApi, self).__init__(inc_ip, inc_port)
        self.api.add_resource(ChainVersionsList, "/")
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(ChainVnf, "/v1/chain/<src_vnf>/<dst_vnf>")
        self.api.add_resource(ChainVnfInterfaces, "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>")
        self.api.add_resource(UnchainVnf, "/v1/unchain/<src_vnf>/<dst_vnf>")
        global ip, port
        ip = self.ip
        port = self.port

    def _start_flask(self):
        global compute, os_net
        logging.info("Starting %s endpoint @ http://%s:%d" % ("ChainDummyApi", self.ip, self.port))
        compute = self.compute
        os_net = self.os_net
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

    def set_os_net(self, net):
        global os_net
        os_net = net
        self.os_net = net

class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut doen") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

class ChainVersionsList(Resource):
    def get(self, id):
        global compute, ip, port
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
            """ % (ip, port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class ChainVnf(Resource):
    def get(self, src_vnf, dst_vnf):
        global compute, os_net
        # check if both VNFs exist
        if src_vnf not in compute.dc.net or dst_vnf not in compute.dc.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")

        try:
            #print compute.dc.net[src_vnf].__dict__
            #print compute.dc.net[dst_vnf].__dict__

            # check if which interface to chain on
            dst_intfs = None
            src_intfs = None

            for intfs in compute.dc.net[src_vnf].intfs.values():
                for dintfs in compute.dc.net[dst_vnf].intfs.values():
                    if intfs.params[intfs.name] == dintfs.params[dintfs.name]:
                        src_intfs = intfs.name
                        dst_intfs = dintfs.name

            os_net.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                        vnf_dst_interface=dst_intfs, bidirectional=True)
        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

class ChainVnfInterfaces(Resource):
    def get(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        global compute, os_net
        # check if both VNFs exist
        if src_vnf not in compute.dc.net or dst_vnf not in compute.dc.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            os_net.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                        vnf_dst_interface=dst_intfs, bidirectional=True)
        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

class UnchainVnf(Resource):
    def get(self, src_vnf, dst_vnf):
        global compute, os_net
        # check if both VNFs exist
        if src_vnf not in compute.dc.net or dst_vnf not in compute.dc.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            os_net.network_action_start(src_vnf, dst_vnf, bidirectional=True)
        except Exception as e:
            logging.exception(u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain", status=500, mimetype="application/json")