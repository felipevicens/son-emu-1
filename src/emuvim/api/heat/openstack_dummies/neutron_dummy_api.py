# -*- coding: UTF-8 -*-

from flask_restful import Resource
from flask import request
from flask import jsonify
import logging
import json
from emuvim.api.heat.heat_parser import HeatParser
from emuvim.api.heat.resources import Stack
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy

compute = None
class NeutronDummyApi(BaseOpenstackDummy):

    def __init__(self,ip,port):
        global compute
        super(NeutronDummyApi, self).__init__(ip, port)
        compute = self.compute