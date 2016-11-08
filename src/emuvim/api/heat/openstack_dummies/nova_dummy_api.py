from flask_restful import Resource
from flask import Response, request
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import logging
import json


class NovaDummyApi(BaseOpenstackDummy):
    def __init__(self, in_ip, in_port, compute):
        super(NovaDummyApi, self).__init__(in_ip, in_port)
        self.compute = compute

        self.api.add_resource(NovaVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(NovaVersionShow, "/v2.1/<id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListServersApi, "/v2.1/<id>/servers",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListServersDetailed, "/v2.1/<id>/servers/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaShowServerDetails, "/v2.1/<id>/servers/<serverid>")
        self.api.add_resource(NovaListFlavors, "/v2.1/<id>/flavors",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavorsDetails, "/v2.1/<id>/flavors/detail",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("NovaDummyApi", self.ip, self.port))
        # add some flavors for good measure
        self.compute.add_flavor('m1.tiny', 1, 512, "MB", 1, "GB")
        self.compute.add_flavor('m1.nano', 1, 64, "MB", 0, "GB")
        self.compute.add_flavor('m1.micro', 1, 128, "MB", 0, "GB")
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut doen") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()

class NovaVersionsList(Resource):

    def __init__(self, api):
        self.api = api

    def get(self):
        try:
            resp = """
                {
                    "versions": [
                        {
                            "id": "v2.1",
                            "links": [
                                {
                                    "href": "http://%s:%d/v2.1/",
                                    "rel": "self"
                                }
                            ],
                            "status": "CURRENT",
                            "version": "2.38",
                            "min_version": "2.1",
                            "updated": "2013-07-23T11:33:21Z"
                        }
                    ]
                }
            """ % (self.api.ip, self.api.port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class NovaVersionShow(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = """
            {
                "version": {
                    "id": "v2.1",
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/",
                            "rel": "self"
                        },
                        {
                            "href": "http://docs.openstack.org/",
                            "rel": "describedby",
                            "type": "text/html"
                        }
                    ],
                    "media-types": [
                        {
                            "base": "application/json",
                            "type": "application/vnd.openstack.compute+json;version=2.1"
                        }
                    ],
                    "status": "CURRENT",
                    "version": "2.38",
                    "min_version": "2.1",
                    "updated": "2013-07-23T11:33:21Z"
                }
            }
            """ % (self.api.ip, self.api.port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class NovaListServersApi(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = dict()
            resp['servers'] = list()
            for stack in self.api.compute.stacks.values():
                for server in stack.servers.values():
                    s = dict()
                    s['id'] = server.id
                    s['name'] = server.name
                    s['links'] = [{'href': "http://%s:%d/v2.1/openstack/servers/%s" % (self.api.ip,
                                                                                       self.api.port,
                                                                                       server.id)}]
                    resp['servers'].append(s)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500


class NovaListServersDetailed(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = dict()
            resp['servers'] = list()
            for stack in self.api.compute.stacks.values():
                for server in stack.servers.values():
                    s = dict()
                    s['id'] = server.id
                    s['name'] = server.name
                    s['links'] = [{'href': "http://%s:%d/v2.1/openstack/servers/%s" % (self.api.ip,
                                                                                       self.api.port,
                                                                                       server.id)}]
                    resp['servers'].append(s)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500


class NovaListFlavors(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = dict()
            resp['flavors'] = list()
            for flavor in self.api.compute.flavors.values():
                f = dict()
                f['id'] = flavor.id
                f['name'] = flavor.name
                f['links'] = [{'href': "http://%s:%d/v2.1/openstack/flavors/%s" % (self.api.ip,
                                                                                   self.api.port,
                                                                                   flavor.id)}]
                resp['flavors'].append(f)
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500


class NovaListFlavorsDetails(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = dict()
            resp['flavors'] = list()
            for flavor in self.api.compute.flavors.values():
                # use the class dict. it should work fine
                # but use a copy so we don't modifiy the original
                f = flavor.__dict__.copy()
                # add additional expected stuff stay openstack compatible
                f['links'] = [{'href': "http://%s:%d/v2.1/openstack/flavors/%s" % (self.api.ip,
                                                                                   self.api.port,
                                                                                   flavor.id)}]
                f['OS-FLV-DISABLED:disabled'] = False
                f['OS-FLV-EXT-DATA:ephemeral'] = 0
                f['os-flavor-access:is_public'] = True
                f['ram'] = flavor.memory
                f['vcpus'] = flavor.cpu
                f['swap'] = 0
                f['disk'] = flavor.storage
                f['rxtx_factor'] = 1.0
                resp['flavors'].append(f)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500


class NovaShowServerDetails(Resource):
    def get(self, id, serverid):
        try:
            resp = dict()
            resp['server'] = dict()

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the server details." % __name__)
            return ex.message, 500
