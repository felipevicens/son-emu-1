# -*- coding: UTF-8 -*-

from flask_restful import Resource
from flask import request
from flask import jsonify
import logging
import json
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from datetime import datetime, timedelta

compute = None
class KeystoneDummyApi(BaseOpenstackDummy):

    def __init__(self,ip,port):
        global compute

        super(KeystoneDummyApi, self).__init__(ip,port)
        compute = self.compute

        self.api.add_resource(KeystoneTokenDefaultScope, "/v2.0/networks")


    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class KeystoneTokenDefaultScope(Resource):
    def get(self):

        logging.debug("API CALL: Keystone - Token Default Scope")
        try:
            return_dict = dict()
            token_dict = dict()

            methods_dict = {"methods":list("password")}
            token_dict.append(methods_dict)

            roles_list = [{"id": "9fe2ff9ee4384b1894a90878d3e92bab","name": "_member_"},
                          {"id": "c703057be878458588961ce9a0ce686b","name": "admin"}]
            token_dict.append(roles_list)

            token_dict.append({"expires_at":datetime.datetime.now() + timedelta(days=7)})

            token_dict.append({"project": {"domain":{"id":"default", "name":"Default"},
                                           "id":"8538a3f13f9541b28c2620eb19065e45", "name":"admin"}})

            token_dict.append({"user": {"domain": {"id": "default","name": "Default"},
                                        "id": "3ec3164f750146be97f21559ee4d9c51","name": "admin"}})

            #TODO here we have to return the supported endpoints

            token_dict.append({"audit_ids": ["yRt0UrxJSs6-WYJgwEMMmg"]})

            token_dict.append({"issued_at": datetime.datetime.now()})

            return_dict.append(token_dict)

            return json.dumps(return_dict), 200

        except Exception as ex:
            logging.exception("Keystone: Default Scope exception.")
            return ex.message, 500