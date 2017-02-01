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
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(GlanceListImagesApi, "/v1/images", "/v2/images",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(GlanceImageByIdApi, "/v1/images/<id>", "/v2/images/<id>",
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


class GlanceListImagesApi(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return {"images": []}  # DEACTIVATED
        try:
            resp = dict()
            resp['images'] = list()
            for image in self.api.compute.images.values():
                f = dict()
                f['id'] = image.id
                f['name'] = str(image.name).replace(":latest", "")
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/images/%s" % (self.api.ip,
                                                                           self.api.port,
                                                                           id,
                                                                           image.id)}]
                resp['images'].append(f)
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not retrieve the list of images." % __name__)
            return ex.message, 500


class GlanceImageByIdApi(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return {"images": []}  # DEACTIVATED
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


