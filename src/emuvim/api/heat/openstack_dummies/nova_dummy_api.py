

from flask_restful import Resource
from flask import Response
from flask import jsonify
import logging
import json
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy

compute = None
class NovaDummyApi(BaseOpenstackDummy):
    def __init__(self, ip, port):
        super(NovaDummyApi, self).__init__(ip, port)
        self.api.add_resource(NovaListApi, "/v2.1/<id>/servers")
        self.compute = None

    def _start_flask(self):
        global compute
        logging.info("Starting %s endpoint @ http://%s:%d" % ("NovaDummyApi", self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

class NovaListApi(Resource):
    global compute
    def get(self, id):
        try:
            #data = json.loads(request.json)
            resp = dict()
            resp['servers'] = list()
            for stack in compute.stacks.values():
                for server in stack.servers.values():
                    s = dict()
                    s['id'] = server.id
                    s['name'] = server.name
                    resp['servers'].append(s)

            return json.dumps(resp), 200

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500


