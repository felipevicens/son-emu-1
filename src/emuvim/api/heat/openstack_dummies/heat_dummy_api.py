# -*- coding: UTF-8 -*-

from flask_restful import Resource
from flask import request
from flask import jsonify
import logging
import json
from emuvim.api.heat.heat_parser import HeatParser
from emuvim.api.heat.resources import Stack

class HeatDummyApi(Resource):


    def post(self, field_identifyer):
        logging.debug("REST CALL: receive file")
        #in request.args  .form .value steht der inhalt der per POST ubergeben wird

        print "Here arrived the following:"
        print json.dumps(request.get_json())


        stack = Stack()
        x = HeatParser()
        x.parse_input(json.dumps(request.get_json()), stack)

        return jsonify(success=True, data={"aaa":"bbb"})