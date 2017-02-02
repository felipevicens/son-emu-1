from flask_restful import Resource
from flask import Response, request
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import logging
import json
import uuid


class GlanceDummyApi(BaseOpenstackDummy):
    def __init__(self, in_ip, in_port, compute):
        super(GlanceDummyApi, self).__init__(in_ip, in_port)
        self.compute = compute
        self.api.add_resource(Shutdown,
                              "/shutdown")
        self.api.add_resource(GlanceListApiVersions,
                              "/versions")
        self.api.add_resource(GlanceSchema,
                              "/v2/schemas/image",
                              "/v2/schemas/metadefs/namespace",
                              "/v2/schemas/metadefs/resource_type")
        self.api.add_resource(GlanceListImagesApi,
                              "/v1/images",
                              "/v1/images/detail",
                              "/v2/images",
                              "/v2/images/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(GlanceImageByIdApi,
                              "/v1/images/<id>",
                              "/v2/images/<id>",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("GlanceDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut down") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


class GlanceListApiVersions(Resource):
    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        resp = dict()
        resp['versions'] = dict()
        versions = [{
            "status": "CURRENT",
            "id": "v2",
            "links": [
                {
                    "href": request.url_root + '/v2',
                    "rel": "self"
                }
            ]
        }]
        resp['versions'] = versions
        return Response(json.dumps(resp), status=200, mimetype='application/json')


class GlanceSchema(Resource):
    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return {}

class GlanceListImagesApi(Resource):
    def __init__(self, api):
        self.api = api

    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['images'] = list()
            limit = 18
            c = 0
            for image in self.api.compute.images.values():
                f = dict()
                f['id'] = image.id
                f['name'] = str(image.name).replace(":latest", "")
                f['checksum'] = "2dad48f09e2a447a9bf852bcd93548c1"
                f['container_format'] = "docker"
                f['disk_format'] = "raw"
                f['size'] = 1
                f['created_at'] = "2016-03-15T15:09:07.000000"
                f['deleted'] = False
                f['deleted_at'] = None
                f['is_public'] = True
                f['min_disk'] = 1
                f['min_ram'] = 128
                f['owner'] = "3dad48f09e2a447a9bf852bcd93548c1"
                f['properties'] = {}
                f['protected'] = False
                f['status'] = "active"
                f['updated_at'] = "2016-03-15T15:09:07.000000"
                f['virtual_size'] = 1
                resp['images'].append(f)
                c+=1
                if c > limit:  # ugly hack to stop buggy glance client to do infinite requests
                    break
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of images." % __name__)
            return ex.message, 500

     def post(self):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))
        logging.warning("Endpoint not implemented")
        return None


class GlanceImageByIdApi(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        logging.warning("Endpoint not implemented")
        return None

    def put(self, id):
        logging.debug("API CALL: %s " % str(self.__class__.__name__))
        logging.warning("Endpoint not implemented")
        return None


