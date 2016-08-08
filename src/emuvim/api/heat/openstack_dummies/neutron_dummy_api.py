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
    global compute

    def __init__(self,ip,port):
        global compute

        super(NeutronDummyApi, self).__init__(ip, port)
        compute = None

        self.api.add_resource(NeutronListNetworks, "/v2.0/networks")
        self.api.add_resource(NeutornShowNetwork, "/v2.0/networks/<network_id>")
        self.api.add_resource(NeutronUpdateNetwork, "/v2.0/networks/<network_id>")
        self.api.add_resource(NeutronListSubnets, "v2.0/subnets")

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class NeutronListNetworks(Resource):

    def get(self):
        global compute

        logging.debug("API CALL: neutron list")
        try:
            network_list = list()
            network_dict = dict()

            for net in compute.networks:
                tmp_network_dict = update_network(net)
                network_list.append(tmp_network_dict)

            network_dict["networks"] = network_list

            return json.dumps(network_dict), 200

        except Exception as ex:
            logging.exception("Neutron: List networks exception.")
            return ex.message, 500


class NeutornShowNetwork(Resource):

    def get(self, network_id):

        def get(self):
            global compute

            logging.debug("API CALL: neutron list")
            try:
                for net in compute.networks:
                    if net.id is network_id:
                        tmp_network_dict = update_network(net)
                        tmp_dict = dict()
                        tmp_dict["network"] = tmp_network_dict
                        return json.dumps(tmp_dict)

                return 'Network not found.', 404

            except Exception as ex:
                logging.exception("Neutron: Show network exception.")
                return ex.message, 500


# TODO maybe add 'Create Network' function


class NeutronUpdateNetwork(Resource):  # TODO currently only the name will be changed

    def put(self, network_id):
        global compute

        logging.debug("API CALL: neutron list")
        try:
            for net in compute.networks:
                if net.id is network_id:
                    tmp_network_dict = request._get_current_object()  # TODO is it realy a dict?
                    #tmp_network_dict["status"] = "ACTIVE"
                    #tmp_network_dict["subnets"] = None
                    net.name = tmp_network_dict["name"]
                    #tmp_network_dict["admin_state_up"] = True
                    #tmp_network_dict["tenant_id"] = "c1210485b2424d48804aad5d39c61b8f"
                    #tmp_network_dict["shared"] = False
                    return json.dumps(tmp_network_dict)

            return 'Network not found.', 404  # TODO which number for not found?

        except Exception as ex:
            logging.exception("Neutron: Show networks exception.")
            return ex.message, 500


# TODO maybe add 'Delete Network' function


class NeutronListSubnets(Resource):

    def get(self):
        None


def update_network(network):
    tmp_network_dict = dict()
    tmp_network_dict["status"] = "ACTIVE"  # TODO do we support inactive networks?
    tmp_network_dict["subnets"] = None  # TODO can we add subnets?
    tmp_network_dict["name"] = network.name
    tmp_network_dict["admin_state_up"] = True  # TODO is it always true?
    tmp_network_dict["tenant_id"] = "c1210485b2424d48804aad5d39c61b8f"  # TODO what should go in here
    tmp_network_dict["id"] = network.id
    tmp_network_dict["shared"] = False  # TODO is it always false?
    return tmp_network_dict