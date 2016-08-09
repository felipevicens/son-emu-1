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
        self.api.add_resource(NeutronShowSubnet, "v2.0/subnets/<subnet_id>")
        self.api.add_resource(NeutronUpdateSubnet, "v2.0/subnets/<subnet_id>")
        self.api.add_resource(NeutronListPorts, "v2.0/ports")
        self.api.add_resource(NeutronShowPort, "v2.0/ports/<port_id>")
        self.api.add_resource(NeutronUpdatePort, "v2.0/ports/<port_id>")

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class NeutronListNetworks(Resource):

    def get(self):
        global compute

        logging.debug("API CALL: Neutron - List networks")
        try:
            network_list = list()
            network_dict = dict()

            for net in compute.stack.nets.values():
                tmp_network_dict = create_network_dict(net)
                network_list.append(tmp_network_dict)

            network_dict["networks"] = network_list

            return json.dumps(network_dict), 200

        except Exception as ex:
            logging.exception("Neutron: List networks exception.")
            return ex.message, 500


class NeutornShowNetwork(Resource):

    def get(self, network_id):
        global compute

        logging.debug("API CALL: Neutron - Show network")
        try:
            for net in compute.stack.nets.values():
                if net.id is network_id:
                    tmp_network_dict = create_network_dict(net)
                    tmp_dict = dict()
                    tmp_dict["network"] = tmp_network_dict
                    return json.dumps(tmp_dict)

            return 'Network not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show network exception.")
            return ex.message, 500


# TODO maybe add 'Create Network' function


class NeutronUpdateNetwork(Resource):  # TODO currently only the name will be changed, dict key has to be updated too

    def put(self, network_id):
        global compute

        logging.debug("API CALL: Neutron - Update network")
        try:
            for net in compute.stack.nets.values():
                if net.id is network_id:
                    tmp_network_dict = request._get_current_object()  # TODO is it really a dict?
                    if "status" in tmp_network_dict["network"]:
                        None  # tmp_network_dict["status"] = "ACTIVE"
                    if "subnets" in tmp_network_dict["network"]:
                        None  # tmp_network_dict["subnets"] = None
                    if "name" in tmp_network_dict["network"] and net.name is not tmp_network_dict["network"]["name"]:
                        old_name = net.name
                        net.name = tmp_network_dict["network"]["name"]
                        compute.stack.nets[net.name] = compute.stack.nets[old_name]
                        del compute.stack.nets[old_name]
                    if "admin_state_up" in tmp_network_dict["network"]:
                        None  # tmp_network_dict["admin_state_up"] = True
                    if "tenant_id" in tmp_network_dict["network"]:
                        None  # tmp_network_dict["tenant_id"] = "c1210485b2424d48804aad5d39c61b8f"
                    if "shared" in tmp_network_dict["network"]:
                        None  # tmp_network_dict["shared"] = False

                    tmp_network_dict = create_network_dict(net)
                    return json.dumps(tmp_network_dict)

            return 'Network not found.', 404  # TODO which number for not found?

        except Exception as ex:
            logging.exception("Neutron: Show networks exception.")
            return ex.message, 500


# TODO maybe add 'Delete Network' function


class NeutronListSubnets(Resource):

    def get(self):
        global compute

        logging.debug("API CALL: Neutron - List subnets")
        try:
            subnet_list = list()
            subnet_dict = dict()

            for net in compute.stack.nets.values():
                tmp_subnet_dict = create_subnet_dict(net)
                subnet_list.append(tmp_subnet_dict)

            subnet_dict["subnets"] = subnet_list

            return json.dumps(subnet_dict), 200

        except Exception as ex:
            logging.exception("Neutron: List subnets exception.")
            return ex.message, 500


class NeutronShowSubnet(Resource):

    def get(self, subnet_id):
        global compute

        logging.debug("API CALL: Neutron - Show subnet")
        try:

            for net in compute.stack.nets.values():
                if net.subnet_id is subnet_id:
                    tmp_subnet_dict = create_subnet_dict(net)
                    tmp_dict = dict()
                    tmp_dict["subnet"] = tmp_subnet_dict
                    return json.dumps(tmp_dict)

            return 'Subnet not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show subnet exception.")
            return ex.message, 500


# TODO maybe add 'Create Subnet' function


class NeutronUpdateSubnet(Resource):

    def put(self, subnet_id):
        global compute

        logging.debug("API CALL: Neutron - Update subnet")
        try:
            for net in compute.stack.nets.values():
                if net.id is subnet_id:
                    subnet_dict = request._get_current_object()  # TODO is it really a dict?
                    if "name" in subnet_dict["subnet"]:
                        net.subnet_name = subnet_dict["subnet"]["name"]
                    if "network_id" in subnet_dict["subnet"]:
                        net.id = subnet_dict["subnet"]["network_id"]
                    if "tenant_id" in subnet_dict["subnet"]:
                        None
                    if "allocation_pools" in subnet_dict["subnet"]:
                        None
                    if "gateway_ip" in subnet_dict["subnet"]:
                        net.gateway_ip = subnet_dict["subnet"]["gateway_ip"]
                    if "ip_version" in subnet_dict["subnet"]:
                        None
                    if "cidr" in subnet_dict["subnet"]:
                        net.cidr = subnet_dict["subnet"]["cidr"]
                    if "id" in subnet_dict["subnet"]:
                        net.subnet_id = subnet_dict["subnet"]["id"]
                    if "enable_dhcp" in subnet_dict["subnet"]:
                        None

                    subnet_dict = create_subnet_dict(net)
                    return json.dumps(subnet_dict)

            return 'Network not found.', 404  # TODO which number for not found?

        except Exception as ex:
            logging.exception("Neutron: Show networks exception.")
            return ex.message, 500


# TODO maybe add 'Delete Subnet' function


class NeutronListPorts(Resource):

    def get(self):
        global compute

        logging.debug("API CALL: Neutron - List ports")
        try:
            port_list = list()
            port_dict = dict()

            for net in compute.stack.nets.values():
                tmp_port_dict = create_subnet_dict(net)
                port_list.append(tmp_port_dict)

            port_dict["ports"] = port_list

            return json.dumps(port_dict), 200

        except Exception as ex:
            logging.exception("Neutron: List ports exception.")
            return ex.message, 500


class NeutronShowPort(Resource):

    def get(self, port_id):
        global compute

        logging.debug("API CALL: Neutron - Show port")
        try:

            for port in compute.stack.ports.values():
                if port.id is port_id:
                    tmp_subnet_dict = create_port_dict(port)
                    tmp_dict = dict()
                    tmp_dict["port"] = tmp_subnet_dict
                    return json.dumps(tmp_dict)

            return 'Port not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show port exception.")
            return ex.message, 500


# TODO maybe add 'Create Port' function


class NeutronUpdatePort(Resource):

    def put(self, port_id):
        global compute

        logging.debug("API CALL: Neutron - Update port")
        try:
            for port in compute.stack.nets.values():
                if port.id is port_id:
                    port_dict = request._get_current_object()  # TODO is it really a dict?
                    if "admin_state_up" in port_dict["port"]:
                        None
                    if "device_id" in port_dict["port"]:
                        None
                    if "device_owner" in port_dict["port"]:
                        None
                    if "fixed_ips" in port_dict["port"]:
                        None
                    if "id" in port_dict["port"]:
                        port.id = port_dict["port"]["id"]
                    if "mac_adress" in port_dict["port"]:
                        port.mac_address = port_dict["port"]["mac_address"]
                    if "name" in port_dict["port"] and port_dict["port"]["name"] is not port.name:
                        old_name = port.name
                        port.name = port_dict["port"]["name"]
                        compute.stack.ports[port.name] = compute.stack.ports[old_name]
                        del compute.stack.ports[old_name]
                    if "network_id" in port_dict["port"]:
                        None
                    if "status" in port_dict["port"]:
                        None
                    if "tenant_id" in port_dict["port"]:
                        None

                    port_dict = create_subnet_dict(port)
                    return json.dumps(port_dict)

            return 'Port not found.', 404  # TODO which number for not found?

        except Exception as ex:
            logging.exception("Neutron: Update port exception.")
            return ex.message, 500


# TODO maybe add 'Delete Port' function


def create_network_dict(network):
    network_dict = dict()
    network_dict["status"] = "ACTIVE"  # TODO do we support inactive networks?
    network_dict["subnets"] = None  # TODO can we add subnets?
    network_dict["name"] = network.name
    network_dict["admin_state_up"] = True  # TODO is it always true?
    network_dict["tenant_id"] = "c1210485b2424d48804aad5d39c61b8f"  # TODO what should go in here
    network_dict["id"] = network.id
    network_dict["shared"] = False  # TODO is it always false?
    return network_dict


def create_subnet_dict(network):
    subnet_dict = dict()
    subnet_dict["name"] = network.subnet_name
    subnet_dict["network_id"] = network.id
    subnet_dict["tenant_id"] = "c1210485b2424d48804aad5d39c61b8f"  # TODO what should go in here?
    subnet_dict["allocation_pools"] = [{"start": "10.10.0.2", "end": "10.10.0.254"}]  # TODO where do we get the real pools?
    subnet_dict["gateway_ip"] = network.gateway_ip
    subnet_dict["ip_version"] = "4"  # TODO which versions do we support?
    subnet_dict["cidr"] = network.cidr
    subnet_dict["id"] = network.subnet_id  # TODO it is currently the gateway_ip. Where do we get the real id?
    subnet_dict["enable_dhcp"] = False  # TODO do we support DHCP?
    return subnet_dict


def create_port_dict(port):
    port_dict = dict()
    port_dict["admin_state_up"] = True  # TODO is it always true?
    port_dict["device_id"] = "257614cc-e178-4c92-9c61-3b28d40eca44"  # TODO find real values
    port_dict["device_owner"] = ""  # TODO do we have such things?
    fixed_ips_list = list()  # TODO add something (floating ip? or some ip that is within the network?)
    port_dict["fixed_ips"] = fixed_ips_list
    port_dict["id"] = port.id
    port_dict["mac_address"] = port.mac_address
    port_dict["name"] = port.name
    port_dict["network_id"] = "6aeaf34a-c482-4bd3-9dc3-7faf36412f12"
    port_dict["status"] = "ACTIVE"  # TODO do we support inactive port?
    port_dict["tenant_id"] = "cf1a5775e766426cb1968766d0191908"  # TODO find real tenant_id
    return port_dict
