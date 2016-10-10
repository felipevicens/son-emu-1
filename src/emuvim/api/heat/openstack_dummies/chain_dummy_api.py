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


class ChainDummyApi(BaseOpenstackDummy):
    def __init__(self, inc_ip, inc_port):
        super(ChainDummyApi, self).__init__(inc_ip, inc_port)
        self.api.add_resource(ChainVersionsList, "/")
        self.api.add_resource(ChainVnf, "/v1/chain/<src_vnf>/<dst_vnf>")
        self.api.add_resource(UnchainVnf, "/v1/unchain/<src_vnf>/<dst_vnf>")
        self.compute = None
        global ip, port
        ip = self.ip
        port = self.port

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % ("ChainDummyApi", self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


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
        global compute
        if src_vnf not in compute.dc.net or dst_vnf not in compute.dc.net:
            return Response(u"At least one VNF does not exist", status=501, mimetype="application/json")
        compute.dc.net.st
        pass

class UnchainVnf(Resource):
    def get(self, src_vnf, dst_vnf):
        global compute
        pass