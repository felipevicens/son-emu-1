# -*- coding: UTF-8 -*-

from flask_restful import Resource
from flask import request
from flask import jsonify
import logging
import json
import uuid
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from datetime import datetime, timedelta

compute = None
ip = None
port = None
logging.basicConfig(level=logging.INFO)
class KeystoneDummyApi(BaseOpenstackDummy):

    def __init__(self,in_ip,in_port):
        global compute, ip, port

        super(KeystoneDummyApi, self).__init__(in_ip,in_port)
        compute = self.compute
        ip = in_ip
        port = in_port
        self.api.add_resource(KeystoneGetToken, "/v2.0/tokens")


    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class KeystoneGetToken(Resource):
    global ip, port
    def post(self):
        logging.debug("API CALL: Keystone - Get token")
        try:
            ret = dict()

            ret['access'] = dict()
            ret['access']['token'] = dict()
            token = ret['access']['token']

            token['issued_at'] = str(datetime.now())
            token['expires'] = str(datetime.now() + timedelta(days=7))
            token['id'] = str(uuid.uuid4())
            token['tenant'] = dict()
            token['tenant']['description'] = None
            token['tenant']['enabled'] = True
            token['tenant']['id'] = request.json['auth']['tenantId']
            token['tenant']['name'] = request.json['auth']['passwordCredentials']['username']

            ret['access']['user'] = dict()
            user = ret['access']['user']
            user['username'] = request.json['auth']['passwordCredentials']['username']
            user['uname'] = request.json['auth']['passwordCredentials']['username']
            user['roles_links'] = list()
            user['id'] = request.json['auth']['tenantId']
            user['roles'] = [{'name' : 'Member'}]

            ret['access']['serviceCatalog'] = dict()
            ret['access']['serviceCatalog'] = [{
                "endpoints": [
                    {
                        "adminURL": "http://%s:%s/v2/%s" %(ip, port +3774, request.json['auth']['tenantId']),
                        "region": "RegionOne",
                        "internalURL": "http://%s:%s/v2/%s" %(ip, port+3774, request.json['auth']['tenantId']),
                        "id": "2dad48f09e2a447a9bf852bcd93548ef",
                        "publicURL": "http://%s:%s/v2/%s" %(ip, port+3774, request.json['auth']['tenantId'])
                    }
                ],
                "endpoints_links": [],
                "type": "compute",
                "name": "nova"
            },
            {
                "endpoints": [
                    {
                        "adminURL": "http://%s:%s/" %(ip, port+4696),
                        "region": "RegionOne",
                        "internalURL": "http://%s:%s/" %(ip, port+4696),
                        "id": "2dad48f09e2a447a9bf852bcd93548cf",
                        "publicURL": "http://%s:%s/" %(ip, port+4696)
                    }
                ],
                "endpoints_links": [],
                "type": "network",
                "name": "neutron"
            },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s/v1/%s" % (ip, port + 3004,request.json['auth']['tenantId']),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s/v1//%s" % (ip, port + 3004, request.json['auth']['tenantId']),
                            "id": "2dad48f09e2a447a9bf852bcd93548bf",
                            "publicURL": "http://%s:%s/v1/%s" % (ip, port + 3004, request.json['auth']['tenantId'])
                        }
                    ],
                    "endpoints_links": [],
                    "type": "orchestration",
                    "name": "heat"
                }
            ]

            ret['access']["metadata"] =  {
                            "is_admin": 0,
                            "roles": [
                                "7598ac3c634d4c3da4b9126a5f67ca2b",
                                "f95c0ab82d6045d9805033ee1fbc80d4"
                            ]
                        },
            ret['access']['trust'] = {
                "trust": {
                    "id": "394998fa61f14736b1f0c1f322882949",
                    "trustee_user_id": "269348fdd9374b8885da1418e0730af1",
                    "trustor_user_id": "3ec3164f750146be97f21559ee4d9c51",
                    "impersonation": False
                }
            }


            print ret

            return json.dumps(ret), 200

        except Exception as ex:
            logging.exception("Keystone: Get token failed.")
            return ex.message, 500


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