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
        self.api.add_resource(HeatShowStack, "/v1/<tenant_id>/stacks/<stack_name>/<stack_id>")
        self.api.add_resource(HeatUpdateStack, "/v1/<tenant_id>/stacks/<stack_name>/<stack_id>")
        self.api.add_resource(HeatDeleteStack, "/v1/<tenant_id>/stacks/<stack_name>/<stack_id>")

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class HeatCreateStack(Resource):
    def post(self, tenant_id):
        global compute, ip, port

        logging.debug("HEAT: Create Stack")

        try:
            stack_dict = request.json

            stack = Stack()
            reader = HeatParser()
            reader.parse_input(stack_dict['template'], stack, compute.dc.label)

            stack.stack_name = stack_dict['stack_name']
            stack.creation_time = str(datetime.now())
            stack.status = "CREATE_COMPLETE"

            return_dict = {"stack": {"id": stack.id,
                                     "links": [
                                        {
                                            "href": "http://%s:%s/v1/%s/stacks/%s"
                                                    %(ip, port, tenant_id, stack.id),
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

        logging.debug("HEAT: Stack List")
        try:
            return_stacks = dict()
            return_stacks['stacks'] = list()
            for stack in compute.stacks.values():
                return_stacks['stacks'].append(
                                {"creation_time": stack.creation_time,
                                  "description":"desc of "+stack.id,
                                  "id": stack.id,
                                  "links": [],
                                  "stack_name": stack.stack_name,
                                  "stack_status": stack.status,
                                  "stack_status_reason": "Stack CREATE completed successfully",
                                  "updated_time": stack.update_time,
                                  "tags": ""
                                })

            return Response(json.dumps(return_stacks), status=200)
        except Exception as ex:
            logging.exception("Heat: List Stack exception.")
            return ex.message, 500

class HeatShowStack(Resource):
    def get(self, tenant_id, stack_name, stack_id):
        global compute, ip, port

        logging.debug("HEAT: Show Stack")
        try:
            stack = compute.stacks[stack_id]
            if stack.stack_name != stack_name:
                return Response('Stack names do not match.', 404)

            return_stack = {
                            "stack": {
                                "capabilities": [],
                                "creation_time": stack.creation_time,
                                "description": "desc of "+stack.id,
                                "id": stack.id,
                                "links": [
                                    {
                                        "href": "http://%s:%s/v1/%s/stacks/%s"
                                                %(ip, port, tenant_id, stack.id),
                                        "rel": "self"
                                    }
                                ],
                                "notification_topics": [],
                                "outputs": [],
                                "parameters": {
                                    "OS::project_id": "3ab5b02f-a01f-4f95-afa1-e254afc4a435",  # add real project id
                                    "OS::stack_id": stack.id,
                                    "OS::stack_name": stack.stack_name
                                },
                                "stack_name": stack.stack_name,
                                "stack_owner": "The owner of the stack.",  # add stack owner
                                "stack_status": stack.status,
                                "stack_status_reason": "The reason for the current status of the stack.",  # add status reason
                                "template_description": "The description of the stack template.",
                                "stack_user_project_id": "The project UUID of the stack user.",
                                "timeout_mins": "",
                                "updated_time": "",
                                "parent": "",
                                "tags": ""
                            }
                        }
            return Response(json.dumps(return_stack), status=200)

        except Exception as ex:
            logging.exception("Heat: Show stack exception.")
            return ex.message, 500

class HeatUpdateStack(Resource):
    def put(self, tenant_id, stack_name, stack_id):
        global compute, ip, port

        logging.debug("Heat: Update Stack")
        try:
            stack = compute.stacks[stack_id]
            if stack.stack_name != stack_name:
                return Response('Stack names do not match.', 404)

            stack_dict = request.json

            # TODO update the stack

            return Response('', 202)

        except Exception as ex:
            logging.exception("Heat: Update Stack exception")
            return ex.message, 500

class HeatDeleteStack(Resource):
    def put(self, tenant_id, stack_name, stack_id):
        global compute, ip, port

        logging.debug("Heat: Delete Stack")
        try:
            if compute.stacks[stack_id].stack_name != stack_name:
                return Response('Stack names do not match.', 404)

            del compute.stacks[stack_id]

            return Response('Deleted Stack: ' + stack_id, 204)

        except Exception as ex:
            logging.exception("Heat: Delete Stack exception")
            return ex.message, 500
