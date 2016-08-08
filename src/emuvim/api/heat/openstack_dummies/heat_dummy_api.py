# -*- coding: UTF-8 -*-

from flask import Flask,jsonify
from flask_restful import Api,Resource
import logging
import json
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy

compute = None
class HeatDummyApi(BaseOpenstackDummy):

    def __init__(self,ip,port):
        global compute
        super(HeatDummyApi, self).__init__(ip, port)
        compute = self.compute


class HeatList(Resource):
    global compute

    def get(self):
        logging.debug("Call to HeatList")
        return jsonify(success=True, data={"aaa": "bbb"})