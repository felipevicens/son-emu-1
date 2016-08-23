# -*- coding: UTF-8 -*-

from flask_restful import Resource
from flask import request, Response
from flask import jsonify
import logging
import json
from emuvim.api.heat.heat_parser import HeatParser
from emuvim.api.heat.resources import Stack
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy

logging.basicConfig(level=logging.DEBUG)
compute = None
class NeutronDummyApi(BaseOpenstackDummy):
    global compute

    def __init__(self,ip,port):
        global compute

        super(NeutronDummyApi, self).__init__(ip, port)
        compute = None

        self.api.add_resource(NeutronListAPIVersions, "/")
        self.api.add_resource(NeutronShowAPIv2Details, "/v2.0")
        self.api.add_resource(NeutronListNetworks, "/v2.0/networks.json")
        self.api.add_resource(NeutronShowNetwork, "/v2.0/networks.json/<network_id>")
        self.api.add_resource(NeutronUpdateNetwork, "/v2.0/networks.json/<network_id>")
        self.api.add_resource(NeutronListSubnets, "/v2.0/subnets.json")
        self.api.add_resource(NeutronShowSubnet, "/v2.0/subnets.json/<subnet_id>")
        self.api.add_resource(NeutronUpdateSubnet, "/v2.0/subnets.json/<subnet_id>")
        self.api.add_resource(NeutronListPorts, "/v2.0/ports.json")
        self.api.add_resource(NeutronShowPort, "/v2.0/ports.json/<port_id>")
        self.api.add_resource(NeutronUpdatePort, "/v2.0/ports.json/<port_id>")

    def _start_flask(self):
        global compute

        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        compute = self.compute
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

class NeutronListAPIVersions(Resource):
    def get(self):
        logging.debug("API CALL: Neutron - List API Versions")
        resp = dict()
        resp['versions'] = dict()

        versions = [{
                "status": "CURRENT",
                "id": "v2.0",
                "links": [
                    {
                        "href": request.url_root + '/v2.0',
                        "rel": "self"
                    }
                ]
            }]
        resp['versions'] = versions

        return Response(json.dumps(resp), status=200, mimetype='application/json')



class NeutronShowAPIv2Details(Resource):
    def get(self):
        logging.debug("API CALL: Neutron - Show API v2 details")
        resp = dict()

        resp['resources'] = dict()
        resp['resources'] = [{
                "links": [
                    {
                        "href": request.url_root + 'v2.0/subnets',
                        "rel": "self"
                    }
                ],
                "name": "subnet",
                "collection": "subnets"
            },
            {
                "links": [
                    {
                        "href": request.url_root + 'v2.0/networks',
                        "rel": "self"
                    }
                ],
                "name": "network",
                "collection": "networks"
            },
            {
                "links": [
                    {
                        "href": request.url_root + 'v2.0/ports',
                        "rel": "self"
                    }
                ],
                "name": "ports",
                "collection": "ports"
            }
        ]

        return Response(json.dumps(resp), status=200, mimetype='application/json')



class NeutronListNetworks(Resource):

    def get(self):
        global compute

        logging.debug("API CALL: Neutron - List networks")
        try:

            if request.args.get('name'):
                show_network = NeutronShowNetwork()
                return show_network.get(request.args.get('name'))

            network_list = list()
            network_dict = dict()

            for stack in compute.stacks.values():
                for net in stack.nets.values():
                    tmp_network_dict = create_network_dict(net)
                    network_list.append(tmp_network_dict)

            network_dict["networks"] = network_list

            return Response(json.dumps(network_dict), status=200, mimetype='application/json')

        except Exception as ex:
            logging.exception("Neutron: List networks exception.")
            return ex.message, 500


class NeutronShowNetwork(Resource):

    def get(self, network_id):
        global compute

        logging.debug("API CALL: Neutron - Show network")
        try:

            for stack in compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == network_id:
                        tmp_network_dict = create_network_dict(net)
                        tmp_dict = dict()
                        tmp_dict["network"] = tmp_network_dict

                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')


            return 'Network not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show network exception.")
            return ex.message, 500


# TODO maybe add 'Create Network' function


class NeutronUpdateNetwork(Resource):  # TODO currently only the name will be changed

    def put(self, network_id):
        global compute

        logging.debug("API CALL: Neutron - Update network")
        try:

            for stack in compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == network_id:
                        network_dict = request.json

                        if "status" in network_dict["network"]:
                            pass  # tmp_network_dict["status"] = "ACTIVE"
                        if "subnets" in network_dict["network"]:
                            pass  # tmp_network_dict["subnets"] = None
                        if "name" in network_dict["network"] and net.name != network_dict["network"]["name"]:
                            old_name = net.name
                            net.name = network_dict["network"]["name"]
                            stack.nets[net.name] = stack.nets[old_name]
                            del stack.nets[old_name]
                        if "admin_state_up" in network_dict["network"]:
                            pass  # tmp_network_dict["admin_state_up"] = True
                        if "tenant_id" in network_dict["network"]:
                            pass  # tmp_network_dict["tenant_id"] = "c1210485b2424d48804aad5d39c61b8f"
                        if "shared" in network_dict["network"]:
                            pass  # tmp_network_dict["shared"] = False

                        network_dict = create_network_dict(net)

                        return Response(json.dumps(network_dict), status=200, mimetype='application/json')


            return 'Network not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show networks exception.")
            return ex.message, 500


# TODO maybe add 'Delete Network' function


class NeutronListSubnets(Resource):

    def get(self):
        global compute

        logging.debug("API CALL: Neutron - List subnets")
        try:
            if request.args.get('name'):
                show_subnet = NeutronShowSubnet()
                return show_subnet.get(request.args.get('name'))

            subnet_list = list()
            subnet_dict = dict()

            for stack in compute.stacks.values():
                for net in stack.nets.values():
                    tmp_subnet_dict = create_subnet_dict(net)
                    subnet_list.append(tmp_subnet_dict)

            subnet_dict["subnets"] = subnet_list
            resp = Response(json.dumps(subnet_dict), status=200)
            resp.headers['Content-Type'] = 'application/json'

            return Response(json.dumps(subnet_dict), status=200, mimetype='application/json')

        except Exception as ex:
            logging.exception("Neutron: List subnets exception.")
            return ex.message, 500


class NeutronShowSubnet(Resource):

    def get(self, subnet_id):
        global compute

        logging.debug("API CALL: Neutron - Show subnet")
        try:
            for stack in compute.stacks.values():
                for net in stack.nets.values():
                    if net.subnet_id == subnet_id:
                        tmp_subnet_dict = create_subnet_dict(net)
                        tmp_dict = dict()
                        tmp_dict["subnet"] = tmp_subnet_dict
                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')

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

            for stack in compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == subnet_id:
                        subnet_dict = request.json

                        if "name" in subnet_dict["subnet"]:
                            net.subnet_name = subnet_dict["subnet"]["name"]
                        if "network_id" in subnet_dict["subnet"]:
                            net.id = subnet_dict["subnet"]["network_id"]
                        if "tenant_id" in subnet_dict["subnet"]:
                            pass
                        if "allocation_pools" in subnet_dict["subnet"]:
                            pass
                        if "gateway_ip" in subnet_dict["subnet"]:
                            net.gateway_ip = subnet_dict["subnet"]["gateway_ip"]
                        if "ip_version" in subnet_dict["subnet"]:
                            pass
                        if "cidr" in subnet_dict["subnet"]:
                            net.cidr = subnet_dict["subnet"]["cidr"]
                        if "id" in subnet_dict["subnet"]:
                            net.subnet_id = subnet_dict["subnet"]["id"]
                        if "enable_dhcp" in subnet_dict["subnet"]:
                            pass

                        subnet_dict = create_subnet_dict(net)

                        return Response(json.dumps(subnet_dict), status=200, mimetype='application/json')

            return 'Network not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show networks exception.")
            return ex.message, 500


# TODO maybe add 'Delete Subnet' function


class NeutronListPorts(Resource):

    def get(self):
        global compute

        logging.debug("API CALL: Neutron - List ports")
        try:
            if request.args.get('name'):
                show_port = NeutronShowPort()
                return show_port.get(request.args.get('name'))

            port_list = list()
            port_dict = dict()

            for stack in compute.stacks.values():
                for net in stack.ports.values():
                    tmp_port_dict = create_port_dict(net)
                    port_list.append(tmp_port_dict)

            port_dict["ports"] = port_list

            return Response(json.dumps(port_dict), status=200, mimetype='application/json')

        except Exception as ex:
            logging.exception("Neutron: List ports exception.")
            return ex.message, 500


class NeutronShowPort(Resource):

    def get(self, port_id):
        global compute

        logging.debug("API CALL: Neutron - Show port")
        try:
            for stack in compute.stacks.values():
                for port in stack.ports.values():
                    if port.id == port_id:
                        tmp_port_dict = create_port_dict(port)
                        tmp_dict = dict()
                        tmp_dict["port"] = tmp_port_dict
                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')

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
            for stack in compute.stacks.values():
                for port in stack.ports.values():
                    if port.id == port_id:
                        port_dict = request.json

                        if "admin_state_up" in port_dict["port"]:
                            pass
                        if "device_id" in port_dict["port"]:
                            pass
                        if "device_owner" in port_dict["port"]:
                            pass
                        if "fixed_ips" in port_dict["port"]:
                            pass
                        if "id" in port_dict["port"]:
                            port.id = port_dict["port"]["id"]
                        if "mac_address" in port_dict["port"]:
                            port.mac_address = port_dict["port"]["mac_address"]
                        if "name" in port_dict["port"] and port_dict["port"]["name"] != port.name:
                            old_name = port.name
                            port.name = port_dict["port"]["name"]
                            stack.ports[port.name] = stack.ports[old_name]
                            del stack.ports[old_name]
                        if "network_id" in port_dict["port"]:
                            pass
                        if "status" in port_dict["port"]:
                            pass
                        if "tenant_id" in port_dict["port"]:
                            pass

                        port_dict = create_port_dict(port)

                        return Response(json.dumps(port_dict), status=200, mimetype='application/json')

            return 'Port not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Update port exception.")
            return ex.message, 500


# TODO maybe add 'Delete Port' function


def create_network_dict(network):
    network_dict = dict()
    network_dict["status"] = "ACTIVE"  # TODO do we support inactive networks?
    network_dict["subnets"] = network.subnet_id  # TODO can we add subnets?
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
    subnet_dict["allocation_pools"] = [calculate_start_and_end_dict(network.cidr)]
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


def calculate_start_and_end_dict(cidr):
    address, suffix = cidr.rsplit('/', 1)
    int_suffix = int(suffix)
    int_address = ip_2_int(address)
    address_space = 2**32 - 1

    for x in range(0, 31-int_suffix):
        address_space = ~(~address_space | (1 << x))

    start = int_address & address_space
    end = start + (2**(32-int_suffix) - 1)

    return {'start': int_2_ip(start), 'end': int_2_ip(end)}


def ip_2_int(ip):
    o = map(int, ip.split('.'))
    res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
    return res


def int_2_ip(int_ip):
    o1 = int(int_ip / 16777216) % 256
    o2 = int(int_ip / 65536) % 256
    o3 = int(int_ip / 256) % 256
    o4 = int(int_ip) % 256
    return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()
