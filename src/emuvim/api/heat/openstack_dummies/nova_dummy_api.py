

from flask_restful import Resource
from flask import Response
from flask import jsonify
import logging
import json
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy

compute = None
ip = None
port = None
class NovaDummyApi(BaseOpenstackDummy):

    def __init__(self, inc_ip, inc_port):
        super(NovaDummyApi, self).__init__(inc_ip, inc_port)
        self.api.add_resource(NovaListApi, "/v2.1/<id>/servers")
        self.api.add_resource(NovaShowServerDetails, "/v2.1/<id>/servers/<serverid>")
        self.api.add_resource(NovaListFlavors, "/v2.1/<id>/flavors")
        self.api.add_resource(NovaShowFlavorDetails, "/v2.1/<id>/flavors/<flavorid>")
        self.compute = None
        global ip, port
        ip = self.ip
        port = self.port

    def _start_flask(self):
        global compute
        logging.info("Starting %s endpoint @ http://%s:%d" % ("NovaDummyApi", self.ip, self.port))
        compute = self.compute
        # add some flavors for good measure
        compute.add_flavor('m1.tiny', 1, 512, "MB", 1, "GB")
        compute.add_flavor('m1.nano', 1, 64, "MB", 0, "GB")
        compute.add_flavor('m1.micro', 1, 128, "MB", 0, "GB")
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

class NovaListApi(Resource):
    def get(self, id):
        global compute, ip, port
        try:
            #data = json.loads(request.json)
            resp = dict()
            resp['servers'] = list()
            for stack in compute.stacks.values():
                for server in stack.servers.values():
                    s = dict()
                    s['id'] = server.id
                    s['name'] = server.name
                    s['links'] = [{'href': "http://%s:%d/v2.1/openstack/servers/%s" % (ip, port, server.id)}]
                    resp['servers'].append(s)

            return json.dumps(resp), 200

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500

class NovaListFlavors(Resource):
    def get(self, id):
        global compute, ip, port
        try:
            resp = dict()
            resp['flavors'] = list()
            for flavor in compute.flavors.values():
                f = dict()
                f['id'] = flavor.id
                f['name'] = flavor.name
                f['links'] = [{'href': "http://%s:%d/v2.1/openstack/flavors/%s" % (ip, port, flavor.id)}]
                resp['flavors'].append(f)

            return json.dumps(resp), 200

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500

class NovaShowFlavorDetails(Resource):
    def get(self, id, flavorid):
        global compute, ip, port
        try:
            resp = dict()
            resp['flavor'] = dict()
            for flavor in compute.flavors.values():
                if flavor.id == flavorid:
                    #use the class dict. it should work fine
                    #but use a copy so we don't modifiy the original
                    f = flavor.__dict__.copy()
                    #add additional expected stuff stay openstack compatible
                    f['links'] = [{'href': "http://%s:%d/v2.1/openstack/flavors/%s" % (ip, port, flavor.id)}]
                    f['OS-FLV-DISABLED:disabled'] = False
                    f['OS-FLV-EXT-DATA:ephemeral'] = 0
                    f['os-flavor-access:is_public'] = True
                    resp['flavor'] = f

            return json.dumps(resp), 200

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500

class NovaShowServerDetails(Resource):
    def get(self, id, serverid):
        global compute, ip, port
        try:
            resp = dict()
            resp['server'] = dict()


            return json.dumps(resp), 200

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500
