# -*- coding: UTF-8 -*-

from flask import request,jsonify, Response
from flask_restful import Api,Resource
import logging
import json
from emuvim.api.heat.resources import Stack
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from datetime import datetime, timedelta
from emuvim.api.heat.heat_parser import HeatParser


compute = None
ip = None
port = None
class HeatDummyApi(BaseOpenstackDummy):
    global compute, ip, port

    def __init__(self, in_ip, in_port):
        global compute

        super(HeatDummyApi, self).__init__(in_ip, in_port)
        self.compute = None
        ip = in_ip
        port = in_port

        self.api.add_resource(HeatCreateStack, "/v1/<tenant_id>/stacks")

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class HeatCreateStack(Resource):
    def post(self, tenant_id):
        global compute, ip, port

        logging.debug("API CALL: Heat - Create Stack")

        try:
            stack_dict = request.json

            stack = Stack()
            reader = HeatParser()
            reader.parse_input(stack_dict['template'], stack, compute.dc.label)

            stack.stack_name = stack_dict['stack_name']

            return_dict = {"stack": {"id": stack.id,
                                     "links": [
                                        {
                                            "href": "http://%s:%s/v1/%s/stacks/%s/"
                                                    %(ip, port,stack.id, stack.stack_name),
                                            "rel": "self"
                                        } ]}}

            compute.add_stack(stack)
            compute.deploy_stack(stack.id)
            return json.dumps(return_dict), 200

        except Exception as ex:
            logging.exception("Heat: Create Stack exception.")
            return ex.message, 500

    def get(self, tenant_id):
        global compute

        logging.debug("API CALL: HEAT - List Stack Data")
        try:
            return_stacks = dict()
            return_stacks['stacks'] = list()
            tmp_stack_list = return_stacks['stacks']
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

            return Response(json.dumps(return_stacks), status=200)
        except Exception as ex:
            logging.exception("Heat: List Stack Dataexception.")
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