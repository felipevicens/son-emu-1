
from flask_restful import Resource
from flask import request
import logging
import heat_parser

class ReceiveConfiguration(Resource):


    def post(self, identifyer):
        logging.debug("REST CALL: receive file")
        #in request.args  .form .value steht der inhalt der per POST ubergeben wird
        print "bereitt"
        print request.values
        input = request.values[identifyer]
        print input


        reader = heat_parser.YAMLReader()
        reader.parse_input(input)
