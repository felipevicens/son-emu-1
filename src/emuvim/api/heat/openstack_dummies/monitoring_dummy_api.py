from flask_restful import Resource
from flask import Response, request
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import logging
import json


class MonitorDummyApi(BaseOpenstackDummy):
    def __init__(self, inc_ip, inc_port, compute):
        super(MonitorDummyApi, self).__init__(inc_ip, inc_port)
        self.compute = compute

        self.api.add_resource(MonitorVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(MonitorVnf, "/v1/monitor/<vnf_name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(Shutdown, "/shutdown")

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("MonitorDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut down") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


class MonitorVersionsList(Resource):

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


class MonitorVnf(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, vnf_name):
        if len(vnf_name) < 3 or 'mn.' != vnf_name[:3]:
            vnf_name = 'mn.' + vnf_name
        # vnf does not exist
        if vnf_name[3:] not in self.api.compute.dc.net:
            return Response(u"MonitorAPI: VNF %s does not exist\n", status=500, mimetype="application/json")

        try:
            monitoring_dict = self.api.compute.monitor_container(vnf_name)
            self.api.compute.display_cpu(vnf_name)
            self.api.compute.display_memory(vnf_name)

            return Response(json.dumps(monitoring_dict)+'\n', status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain\n", status=500, mimetype="application/json")
