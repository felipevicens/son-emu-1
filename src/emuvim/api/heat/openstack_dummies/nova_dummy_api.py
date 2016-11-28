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
        self.api.add_resource(NovaShowServerDetails, "/v2.1/<id>/servers/<serverid>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavors, "/v2.1/<id>/flavors/",
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
        self.compute.add_flavor('m1.small', 1, 1024, "MB", 2, "GB")
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
            for server in self.api.compute.computeUnits.values():
                s = server.create_server_dict(self.api.compute)
                s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
                                                                            server.id)}]

                resp['servers'].append(s)

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of servers." % __name__)
            return ex.message, 500

    def post(self, id):
        '''
        Creates a server instance
        :param id: tenant id
        :return:
        '''
        try:
            req = request.json
            server_dict = request.json['server']
            networks = server_dict.get('networks', None)
            if self.api.compute.find_server_by_name_or_id(server_dict['name']) is not None:
                return Response("Server with name %s already exists." % server_dict['name'], status=409)
            # TODO: not finished!
            resp = dict()
            name = str(self.api.compute.dc.label) + "_man_" + server_dict["name"][0:12]
            server = self.api.compute.create_server(name)
            server.full_name = str(self.api.compute.dc.label) + "_man_" + server_dict["name"]

            for flavor in self.api.compute.flavors.values():
                if flavor.id == server_dict.get('flavorRef', ''):
                     server.flavor = flavor.name
            for image in self.api.compute.images.values():
                if image.id == server_dict['imageRef']:
                    server.image = image.name

            if networks is not None:
                for net in networks:
                    port = self.api.compute.find_port_by_name_or_id(net.get('port', ""))
                    if port is not None:
                        server.port_names.append(port.name)
                    else:
                        return Response("Currently only networking by port is supported.", status=400)

            self.api.compute._start_compute(server)

            return NovaShowServerDetails(self.api).get(id, server.id)

        except Exception as ex:
            logging.exception(u"%s: Could not create the server." % __name__)
            return ex.message, 500


class NovaListServersDetailed(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        try:
            resp = {"servers": list()}
            for server in self.api.compute.computeUnits.values():
                s = server.create_server_dict(self.api.compute)
                s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
                                                                            server.id)}]
                flavor = self.api.compute.flavors[server.flavor]
                s['flavor'] = {
                    "id": flavor.id,
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                         self.api.port,
                                                                         id,
                                                                         flavor.id),
                            "rel": "bookmark"
                        }
                    ]
                }
                image = self.api.compute.images[server.image]
                s['image'] = {
                    "id": image.id,
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                        self.api.port,
                                                                        id,
                                                                        image.id),
                            "rel": "bookmark"
                        }
                    ]
                }

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
                f = flavor.__dict__.copy()
                f['id'] = flavor.id
                f['name'] = flavor.name
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
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
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                            self.api.port,
                                                                            id,
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
                    if f.id == flavorid:
                        flavor = f
                        break
            resp['flavor']['id'] = flavor.id
            resp['flavor']['name'] = flavor.name
            resp['flavor']['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                                     self.api.port,
                                                                                     id,
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
            for image in self.api.compute.images.values():
                f = dict()
                f['id'] = image.id
                f['name'] = image.name
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                           self.api.port,
                                                                           id,
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
            for image in self.api.compute.images.values():
                # use the class dict. it should work fine
                # but use a copy so we don't modifiy the original
                f = image.__dict__.copy()
                # add additional expected stuff stay openstack compatible
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                           self.api.port,
                                                                           id,
                                                                           image.id)}]
                f['metadata'] = {
                    "architecture": "x86_64",
                    "auto_disk_config": "True",
                    "kernel_id": "nokernel",
                    "ramdisk_id": "nokernel"
                }
                resp['images'].append(f)

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
            i = resp['image'] = dict()
            for image in self.api.compute.images.values():
                if image.id == imageid or image.name == imageid:
                    i['id'] = image.id
                    i['name'] = image.name

                    return Response(json.dumps(resp), status=200, mimetype="application/json")

            return Response("Image with id or name %s does not exists." % imageid, status=404)

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve image with id %s." % (__name__, imageid))
            return ex.message, 500


class NovaShowServerDetails(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, serverid):
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response("Server with id or name %s does not exists." % serverid, status=404)
            s = server.create_server_dict()
            s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (self.api.ip,
                                                                        self.api.port,
                                                                        id,
                                                                        server.id)}]

            flavor = self.api.compute.flavors[server.flavor]
            s['flavor'] = {
                "id": flavor.id,
                "links": [
                    {
                        "href": "http://%s:%d/v2.1/%s/flavors/%s" % (self.api.ip,
                                                                     self.api.port,
                                                                     id,
                                                                     flavor.id),
                        "rel": "bookmark"
                    }
                ]
            }
            image = self.api.compute.images[server.image]
            s['image'] = {
                "id": image.id,
                "links": [
                    {
                        "href": "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                    self.api.port,
                                                                    id,
                                                                    image.id),
                        "rel": "bookmark"
                    }
                ]
            }

            return Response(json.dumps({'server': s}), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the server details." % __name__)
            return ex.message, 500
