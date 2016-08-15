# -*- coding: UTF-8 -*-

from flask import request,jsonify
from flask_restful import Api,Resource
import logging
import json
from resources import Stack
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from datetime import datetime, timedelta


compute = None
class HeatDummyApi(BaseOpenstackDummy):
    global compute

    def __init__(self, ip, port):
        global compute

        super(HeatDummyApi, self).__init__(ip, port)
        compute = None

        self.api.add_resource(HeatCreateStack, "/v2.0/networks/<tenant_id>")
        self.api.add_resource(HeatAdoptStack, "/v2.0/networks/<tenant_id>")
        self.api.add_resource(HeatListStackData, "/v2.0/networks/<tenant_id>")

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class HeatCreateStack(Resource):
    def post(self, tenant_id):
        global compute

        logging.debug("API CALL: Heat - Create Stack")

        try:
            stack_dict = request.json
            stack = Stack()

            return_dict = {"stack": {"id": stack.id,
                                     "links": [
                                        {
                                            "href": "http://192.168.123.200:8004/v1/eb1c63a4f77141548385f113a28f0f52/stacks/teststack/"+stack.id,
                                            "rel": "self"
                                        } ]}}#TODO find out the URL of the stack

            compute.stacks.append(stack)

            return json.dumps(return_dict), 200

        except Exception as ex:
            logging.exception("Heat: Create Stack exception.")
            return ex.message, 500


class HeatAdoptStack(Resource):
    def post(self, tenant_id):
        global compute

        logging.debug("API CALL: Heat - Adopt Stack")

        try:
            request_dict = request.json
            for stack in compute.stacks.values():
                if stack.id == request_dict["id"]:
                    stack_to_modify = stack
                    pass #TODO does this quit the for-loop?


            #TODO do we need to update anything here?


            return_dict = {"stack": {"id": stack.id,
                                     "links": [
                                         {
                                             "href": "http://192.168.123.200:8004/v1/eb1c63a4f77141548385f113a28f0f52/stacks/teststack/" + stack.id,
                                             "rel": "self"
                                         }]}}  # TODO find out the URL of the stack

            compute.stacks.append(stack)

            return json.dumps(return_dict), 200

        except Exception as ex:
            logging.exception("Heat: Adopt Stack exception.")
            return ex.message, 500

class HeatListStackData(Resource):

    def get(self, tenant_id):
        global compute

        logging.debug("API CALL: HEAT - List Stack Data")
        try:
            tmp_stack_list = list()
            for stack in compute.stacks.values():
                tmp_stack_list = {"creation_time":datetime.datetime.now() - timedelta(days=7),
                                  "description":"desc of "+stack.id,
                                  "id": stack.id,
                                  "links": [],
                                  "stack_name": "simple_stack",
                                  "stack_status": "CREATE_COMPLETE",
                                  "stack_status_reason": "Stack CREATE completed successfully",
                                  "updated_time": "",
                                  "tags": ""
                                  }

            return json.dumps(tmp_stack_list),200



        except Exception as ex:
            logging.exception("Heat: List Stack Dataexception.")
            return ex.message, 500