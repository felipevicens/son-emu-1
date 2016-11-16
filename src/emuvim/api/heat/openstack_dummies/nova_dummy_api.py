from flask_restful import Resource
from flask import Response, request
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import logging
import json
from datetime import datetime


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
        self.api.add_resource(NovaListFlavorById, "/v2.1/<id>/flavors/<flavorid>",
                              resource_class_kwargs={'api': self})

        self.api.add_resource(NovaListImages, "/v2.1/<id>/images",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImagesDetails, "/v2.1/<id>/images/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImageById, "/v2.1/<id>/images/<imageid>",
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

    def post(self, id):
        try:
            req = request.json

            flavor = request.json['server'].get('flavorRef','')
            image = request.json['server'].get('imageRef', '')
            print req
            resp = dict()
            s = resp['server'] = dict()
            s['name'] = request.json['server'].get('name', '')

        except Exception as ex:
            logging.exception(u"%s: Could not createthe server." % __name__)
            return ex.message, 500


class NovaListServersDetailed(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = dict()
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

class NovaListFlavorById(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id, flavorid):
        try:
            resp = dict()
            resp['flavor'] = dict()
            flavor = self.api.compute.flavors.get(flavorid, None)
            if flavor is None:
                for f in self.api.compute.flavors.values():
                    if f.name == flavorid:
                        flavor = f
                        break
            resp['flavor']['id'] = flavor.id
            resp['flavor']['name'] = flavor.name
            resp['flavor']['links'] = [{'href': "http://%s:%d/v2.1/openstack/flavors/%s" % (self.api.ip,
                                                                               self.api.port,
                                                                               flavor.id)}]
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve flavor with id %s" % (__name__, flavorid))
            return ex.message, 500

class NovaListImages(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = dict()
            resp['images'] = list()
            # add a dummy server to create images from.
            # call 1-800-dirtyhack
            s = dict()
            s['id'] = "1"
            s['name'] = "CREATE-IMAGE"
            s['links'] = [{'href': "http://%s:%d/v2.1/openstack/servers/1" % (self.api.ip,
                                                                               self.api.port)}]
            resp['images'].append(s)
            for image in self.api.compute.images.values():
                f = dict()
                f['id'] = image.id
                f['name'] = image.name
                f['links'] = [{'href': "http://%s:%d/v2.1/openstack/images/%s" % (self.api.ip,
                                                                                   self.api.port,
                                                                                   image.id)}]
                resp['images'].append(f)
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of images." % __name__)
            return ex.message, 500


class NovaListImagesDetails(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = dict()
            resp['images'] = list()
            # add a dummy server to create images from.
            # call 1-800-dirtyhack
            s = dict()
            s['id'] = "1"
            s['name'] = "CREATE-IMAGE"
            s['status'] = "INACTIVE"
            s['created'] = str(datetime.now())
            s['updated'] = str(datetime.now())
            s['links'] = [{'href': "http://%s:%d/v2.1/openstack/servers/1" % (self.api.ip,
                                                                               self.api.port)}]
            resp['images'].append(s)
            for image in self.api.compute.images.values():
                # use the class dict. it should work fine
                # but use a copy so we don't modifiy the original
                f = image.__dict__.copy()
                # add additional expected stuff stay openstack compatible
                f['links'] = [{'href': "http://%s:%d/v2.1/openstack/images/%s" % (self.api.ip,
                                                                                   self.api.port,
                                                                                   image.id)}]
                f['minDisk'] = 0
                f['id'] = f.id
                f['minRam'] = 0
                f['created'] = str(datetime.now())
                f['updated'] = str(datetime.now())
                resp['flavors'].append(f)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of images." % __name__)
            return ex.message, 500

class NovaListImageById(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, imageid):
        '''
        Gets an image by id from the emulator with openstack nova compliant return values.
        :param id: tenantid, we ignore this most of the time
        :param imageid: id of the image. If it is 1 the dummy CREATE-IMAGE is returned
        :return:
        '''
        try:
            resp = dict()
            resp['image'] = dict()
            # add a dummy server to create images from.
            # call 1-800-dirtyhack
            s = resp['image']
            if str(imageid) == "1":
                s['id'] = "1"
                s['name'] = "CREATE-IMAGE"
                s['status'] = "INACTIVE"
                s['created'] = str(datetime.now())
                s['updated'] = str(datetime.now())
                s['links'] = [{'href': "http://%s:%d/v2.1/openstack/images/1" % (self.api.ip,
                                                                                   self.api.port)}]
                s['metadata'] = {
                        "architecture": "x86_64",
                        "auto_disk_config": "True",
                        "kernel_id": "nokernel",
                        "ramdisk_id": "nokernel"
                }
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve image with id %s." % (__name__, imageid))
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
