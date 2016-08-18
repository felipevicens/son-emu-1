# -*- coding: UTF-8 -*-

from flask_restful import Resource
from flask import request, Response
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
    def __init__(self, in_ip, in_port):
        global compute, ip, port

        super(KeystoneDummyApi, self).__init__(in_ip, in_port)
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
        # everything is hardcoded here
        # to work with this keystone setup you need the following parameters
        # OS_AUTH_URL=http://<ip>:<port>/v2.0
        # OS_IDENTITY_API_VERSION=2.0
        # OS_TENANT_ID=fc394f2ab2df4114bde39905f800dc57
        # OS_REGION_NAME=regionOne
        # OS_AUTH_TOKEN=aaaaa-bbbbb-ccccc-dddd
        # OS_USER_ID=9a6590b2ab024747bc2167c4e064d00d
        # OS_USERNAME=username

        logging.debug("API CALL: Keystone - Get token")
        try:
            ret = dict()
            ret['access'] = dict()
            ret['access']['token'] = dict()
            token = ret['access']['token']

            token['issued_at'] = str(datetime.now())
            token['expires'] = str(datetime.now() + timedelta(days=7))
            token['id'] = "435345"
            token['tenant'] = dict()
            token['tenant']['description'] = None
            token['tenant']['enabled'] = True
            token['tenant']['id'] = "fc394f2ab2df4114bde39905f800dc57"
            token['tenant']['name'] = "tenantName"

            ret['access']['user'] = dict()
            user = ret['access']['user']
            user['username'] = "username"
            user['name'] = "tenantName"
            user['roles_links'] = list()
            user['id'] = "fc394f2ab2df4114bde39905f800dc57"
            user['roles'] = [{'name' : 'Member'}]

            ret['access']['region_name'] = "RegionOne"

            ret['access']['serviceCatalog'] = [{
                "endpoints": [
                    {
                        "adminURL": "http://%s:%s/v2/%s" %(ip, port +3774, user['id'] ),
                        "region": "RegionOne",
                        "internalURL": "http://%s:%s/v2/%s" %(ip, port+3774, user['id'] ),
                        "id": "2dad48f09e2a447a9bf852bcd93548ef",
                        "publicURL": "http://%s:%s/v2/%s" %(ip, port+3774, user['id'] )
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
                            "adminURL": "http://%s:%s/v1/%s" % (ip, port + 3004, user['id'] ),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s/v1/%s" % (ip, port + 3004, user['id'] ),
                            "id": "2dad48f09e2a447a9bf852bcd93548bf",
                            "publicURL": "http://%s:%s/v1/%s" % (ip, port + 3004, user['id'] )
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
                    "id": "394998fa61f14736b1f0c1f322882949",
                    "trustee_user_id": "269348fdd9374b8885da1418e0730af1",
                    "trustor_user_id": "3ec3164f750146be97f21559ee4d9c51",
                    "impersonation": False
            }
            print json.dumps(ret)
            resp = Response(json.dumps(ret), status=200)

            return resp

        except Exception as ex:
            logging.exception("Keystone: Get token failed.")
            return ex.message, 500