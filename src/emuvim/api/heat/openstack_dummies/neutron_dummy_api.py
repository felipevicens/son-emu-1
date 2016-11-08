# -*- coding: UTF-8 -*-

from flask_restful import Resource
from flask import request, Response
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from ..resources import Net, Port
from mininet.link import Link
from datetime import datetime
import logging
import json
import uuid


logging.basicConfig(level=logging.DEBUG)


class NeutronDummyApi(BaseOpenstackDummy):

    def __init__(self, ip, port, compute):
        super(NeutronDummyApi, self).__init__(ip, port)
        self.compute = compute

        self.api.add_resource(NeutronListAPIVersions, "/")
        self.api.add_resource(Shutdown, "/shutdown")
        self.api.add_resource(NeutronShowAPIv2Details, "/v2.0")
        self.api.add_resource(NeutronListNetworks, "/v2.0/networks.json", "/v2.0/networks",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronShowNetwork, "/v2.0/networks/<network_id>.json", "/v2.0/networks/<network_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronCreateNetwork, "/v2.0/networks.json", "/v2.0/networks",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronUpdateNetwork, "/v2.0/networks/<network_id>.json", "/v2.0/networks/<network_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronDeleteNetwork, "/v2.0/networks/<network_id>.json", "/v2.0/networks/<network_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronListSubnets, "/v2.0/subnets.json", "/v2.0/subnets",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronShowSubnet, "/v2.0/subnets/<subnet_id>.json", "/v2.0/subnets/<subnet_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronCreateSubnet, "/v2.0/subnets.json", "/v2.0/subnets",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronUpdateSubnet, "/v2.0/subnets/<subnet_id>.json", "/v2.0/subnets/<subnet_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronDeleteSubnet, "/v2.0/subnets/<subnet_id>.json", "/v2.0/subnets/<subnet_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronListPorts, "/v2.0/ports.json", "/v2.0/ports",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronShowPort, "/v2.0/ports/<port_id>.json", "/v2.0/ports/<port_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronCreatePort, "/v2.0/ports.json", "/v2.0/ports",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronUpdatePort, "/v2.0/ports/<port_id>.json", "/v2.0/ports/<port_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronDeletePort, "/v2.0/ports/<port_id>.json", "/v2.0/ports/<port_id>",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class Shutdown(Resource):

    def get(self):
        logging.debug(("%s is beeing shut down") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


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

    def __init__(self, api):
        self.api = api

    def get(self):
        logging.debug("API CALL: Neutron - List networks")
        try:

            if request.args.get('name'):
                tmp_network = NeutronShowNetwork(self.api)
                return tmp_network.get_network(request.args.get('name'), True)
            id_list = request.args.getlist('id')
            if len(id_list) == 1:
                tmp_network = NeutronShowNetwork(self.api)
                return tmp_network.get_network(request.args.get('id'), True)

            network_list = list()
            network_dict = dict()

            if len(id_list) == 0:
                for stack in self.api.compute.stacks.values():
                    for net in stack.nets.values():
                        tmp_network_dict = create_network_dict(net)
                        network_list.append(tmp_network_dict)
            else:
                for stack in self.api.compute.stacks.values():
                    for net in stack.nets.values():
                        if net.id in id_list:
                            tmp_network_dict = create_network_dict(net)
                            network_list.append(tmp_network_dict)

            network_dict["networks"] = network_list

            return Response(json.dumps(network_dict), status=200, mimetype='application/json')

        except Exception as ex:
            logging.exception("Neutron: List networks exception.")
            return ex.message, 500


class NeutronShowNetwork(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, network_id):
        return self.get_network(network_id, False)

    def get_network(self, network_id, as_list):
        logging.debug("API CALL: Neutron - Show network")
        try:
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == network_id:
                        tmp_network_dict = create_network_dict(net)
                        tmp_dict = dict()
                        if as_list:
                            tmp_dict["networks"] = [tmp_network_dict]
                        else:
                            tmp_dict["network"] = tmp_network_dict

                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')

            return 'Network not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show network exception.")
            return ex.message, 500


class NeutronCreateNetwork(Resource):

    def __init__(self, api):
        self.api = api

    def post(self):
        logging.debug("API CALL: Neutron - Create network")
        try:
            for stack in self.api.compute.stacks.values():  # TODO which stack should i use to create the network???
                network_dict = request.json
                name = network_dict['network']['name']
                if name not in stack.nets:
                    stack.nets[name] = Net(name)
                    stack.nets[name].id = str(uuid.uuid4())
                else:
                    return 'Network already exists.', 400

                tmp_network_dict = create_network_dict(stack.nets[name])
                tmp_dict = dict()
                tmp_dict["network"] = tmp_network_dict

                return Response(json.dumps(tmp_dict), status=201, mimetype='application/json')

            return 'No Stack found to create the Network.', 404
        except Exception as ex:
            logging.exception("Neutron: Create network excepiton.")
            return ex.message, 500


class NeutronUpdateNetwork(Resource):

    def __init__(self, api):
        self.api = api

    def put(self, network_id): # TODO currently only the name will be changed
        logging.debug("API CALL: Neutron - Update network")
        try:
            for stack in self.api.compute.stacks.values():
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
                        tmp_dict = dict()
                        tmp_dict["network"] = network_dict


                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')

            return 'Network not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show networks exception.")
            return ex.message, 500


class NeutronDeleteNetwork(Resource):

    def __init__(self, api):
        self.api = api

    def delete(self, network_id):
        logging.debug("API CALL: Neutron - Delete network")
        try:
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == network_id:
                        delete_subnet = NeutronDeleteSubnet(self.api)
                        response_string, response_id = delete_subnet.delete(net.subnet_id)

                        if response_id != 204 and response_id != 404:
                            return response_string, response_id

                        net_name = net.name
                        del stack.nets[net_name]

                        return 'Network ' + str(network_id) + ' deleted.', 204

            return 'Could not find network. (' + network_id + ')', 404

        except Exception as ex:
            logging.exception("Neutron: Delete network exception.")
            return ex.message, 500


class NeutronListSubnets(Resource):

    def __init__(self, api):
        self.api = api

    def get(self):
        logging.debug("API CALL: Neutron - List subnets")
        try:
            if request.args.get('name'):
                show_subnet = NeutronShowSubnet(self.api)
                return show_subnet.get_subnet(request.args.get('name'), True)
            id_list = request.args.getlist('id')
            if len(id_list) == 1:
                show_subnet = NeutronShowSubnet(self.api)
                return show_subnet.get_subnet(id_list[0], True)

            subnet_list = list()
            subnet_dict = dict()

            if len(id_list) == 0:
                for stack in self.api.compute.stacks.values():
                    for net in stack.nets.values():
                        if net.subnet_id is not None:
                            tmp_subnet_dict = create_subnet_dict(net)
                            subnet_list.append(tmp_subnet_dict)
            else:
                for stack in self.api.compute.stacks.values():
                    for net in stack.nets.values():
                        if net.subnet_id in id_list:
                            tmp_subnet_dict = create_subnet_dict(net)
                            subnet_list.append(tmp_subnet_dict)

            subnet_dict["subnets"] = subnet_list

            return Response(json.dumps(subnet_dict), status=200, mimetype='application/json')

        except Exception as ex:
            logging.exception("Neutron: List subnets exception.")
            return ex.message, 500


class NeutronShowSubnet(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, subnet_id):
        return self.get_subnet(subnet_id, False)

    def get_subnet(self, subnet_id, as_list):
        logging.debug("API CALL: Neutron - Show subnet")
        try:
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.subnet_id == subnet_id:
                        tmp_subnet_dict = create_subnet_dict(net)
                        tmp_dict = dict()
                        if as_list:
                            tmp_dict["subnets"] = [tmp_subnet_dict]
                        else:
                            tmp_dict["subnet"] = tmp_subnet_dict
                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')

            return 'Subnet not found. (' + subnet_id + ')', 404

        except Exception as ex:
            logging.exception("Neutron: Show subnet exception.")
            return ex.message, 500


class NeutronCreateSubnet(Resource):

    def __init__(self, api):
        self.api = api

    def post(self):
        logging.debug("API CALL: Neutron - Create subnet")
        try:
            subnet_dict = request.json
            net_id = subnet_dict['subnet']['network_id']
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == net_id:
                        if net.subnet_id is not None:
                            return 'Only one subnet per network is supported', 409

                        if "cidr" in subnet_dict["subnet"]:
                            if not net.set_cidr(subnet_dict["subnet"]["cidr"]):
                                return 'Wrong CIDR format.', 400
                        else:
                            return 'No CIDR found.', 400
                        if "name" in subnet_dict["subnet"]:
                            net.subnet_name = subnet_dict["subnet"]["name"]
                        if "tenant_id" in subnet_dict["subnet"]:
                            pass
                        if "allocation_pools" in subnet_dict["subnet"]:
                            pass
                        if "gateway_ip" in subnet_dict["subnet"]:
                            net.gateway_ip = subnet_dict["subnet"]["gateway_ip"]
                        if "ip_version" in subnet_dict["subnet"]:
                            pass
                        if "id" in subnet_dict["subnet"]:
                            net.subnet_id = subnet_dict["subnet"]["id"]
                        else:
                            net.subnet_id = str(uuid.uuid4())
                        if "enable_dhcp" in subnet_dict["subnet"]:
                            pass

                        tmp_subnet_dict = create_subnet_dict(net)
                        tmp_dict = dict()
                        tmp_dict["subnet"] = tmp_subnet_dict
                        return Response(json.dumps(tmp_dict), status=201, mimetype='application/json')

            return 'Could not find network.', 404

        except Exception as ex:
            logging.exception("Neutron: Create network excepiton.")
            return ex.message, 500


class NeutronUpdateSubnet(Resource):

    def __init__(self, api):
        self.api = api

    def put(self, subnet_id):
        logging.debug("API CALL: Neutron - Update subnet")
        try:
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.subnet_id == subnet_id:
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
                            net.set_cidr(subnet_dict["subnet"]["cidr"])
                        if "id" in subnet_dict["subnet"]:
                            net.subnet_id = subnet_dict["subnet"]["id"]
                        if "enable_dhcp" in subnet_dict["subnet"]:
                            pass

                        net.subnet_update_time = str(datetime.now())
                        tmp_subnet_dict = create_subnet_dict(net)
                        tmp_dict = dict()
                        tmp_dict["subnet"] = tmp_subnet_dict
                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')


            return 'Network not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Show networks exception.")
            return ex.message, 500


class NeutronDeleteSubnet(Resource):

    def __init__(self, api):
        self.api = api

    def delete(self, subnet_id):
        logging.debug("API CALL: Neutron - Delete subnet")
        try:
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.subnet_id == subnet_id:
                        for server in stack.servers.values():
                            for port_name in server.port_names:
                                port = stack.ports[port_name]
                                if port.net_name == net.name:
                                    port.ip_address = None
                                    self.api.compute.dc.net.removeLink(
                                        link=None,
                                        node1=self.api.compute.dc.containers[server.name],
                                        node2=self.api.compute.dc.switch)

                        net.subnet_id = None
                        net.subnet_name = None
                        net.set_cidr(None)
                        net.start_end_dict = None
                        net.reset_issued_ip_addresses()

                        return 'Subnet ' + str(subnet_id) + ' deleted.', 204

            return 'Could not find subnet.', 404
        except Exception as ex:
            logging.exception("Neutron: Delete subnet exception.")
            return ex.message, 500


class NeutronListPorts(Resource):

    def __init__(self, api):
        self.api = api

    def get(self):
        logging.debug("API CALL: Neutron - List ports")
        try:
            if request.args.get('name'):
                show_port = NeutronShowPort(self.api)
                return show_port.get_port(request.args.get('name'), True)
            id_list = request.args.getlist('id')
            if len(id_list) == 1:
                show_port = NeutronShowPort(self.api)
                return show_port.get_port(request.args.get('id'), True)

            port_list = list()
            port_dict = dict()

            if len(id_list) == 0:
                for stack in self.api.compute.stacks.values():
                    for port in stack.ports.values():
                        tmp_port_dict = create_port_dict(port, self.api.compute)
                        port_list.append(tmp_port_dict)
            else:
                for stack in self.api.compute.stacks.values():
                    for port in stack.ports.values():
                        if port.id in id_list:
                            tmp_port_dict = create_port_dict(port, self.api.compute)
                            port_list.append(tmp_port_dict)

            port_dict["ports"] = port_list

            return Response(json.dumps(port_dict), status=200, mimetype='application/json')

        except Exception as ex:
            logging.exception("Neutron: List ports exception.")
            return ex.message, 500


class NeutronShowPort(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, port_id):
        return self.get_port(port_id, False)

    def get_port(self, port_id, as_list):
        logging.debug("API CALL: Neutron - Show port")
        try:
            for stack in self.api.compute.stacks.values():
                for port in stack.ports.values():
                    if port.id == port_id:
                        tmp_port_dict = create_port_dict(port, self.api.compute)
                        tmp_dict = dict()
                        if as_list:
                            tmp_dict["ports"] = [tmp_port_dict]
                        else:
                            tmp_dict["port"] = tmp_port_dict
                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')

            return 'Port not found. (' + port_id + ')', 404

        except Exception as ex:
            logging.exception("Neutron: Show port exception.")
            return ex.message, 500


class NeutronCreatePort(Resource):

    def __init__(self, api):
        self.api = api

    def post(self):
        logging.debug("API CALL: Neutron - Create port")
        try:
            port_dict = request.json
            if 'name' in port_dict['port']:
                name = port_dict['port']['name']
            else:
                name = 'MEINNNZZZZZZ' +\
                       str(len(self.api.compute.stacks[self.api.compute.stacks.keys()[0]].ports)-1)  # TODO add some real name
            net_id = port_dict['port']['network_id']
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == net_id:
                        port = None
                        if name not in stack.ports:
                            port = Port(name)
                            stack.ports[name] = port
                        else:
                            return 'Port name already exists.', 400

                        port.net_name = net.name
                        port.ip_address = net.get_new_ip_address(name)

                        if "admin_state_up" in port_dict["port"]:
                            pass
                        if "device_id" in port_dict["port"]:
                            pass
                        if "device_owner" in port_dict["port"]:
                            pass
                        if "fixed_ips" in port_dict["port"]:
                            pass
                        if "id" in port_dict["port"]:
                            stack.ports[name].id = port_dict["port"]["id"]
                        else:
                            stack.ports[name].id = str(uuid.uuid4())
                        if "mac_address" in port_dict["port"]:
                            stack.ports[name].mac_address = port_dict["port"]["mac_address"]
                        if "status" in port_dict["port"]:
                            pass
                        if "tenant_id" in port_dict["port"]:
                            pass

                        tmp_port_dict = create_port_dict(stack.ports[name], self.api.compute)
                        tmp_dict = dict()
                        tmp_dict["port"] = tmp_port_dict

                        return Response(json.dumps(tmp_dict), status=201, mimetype='application/json')

            return 'Could not find network.', 404

        except Exception as ex:
            logging.exception("Neutron: Show port exception.")
            return ex.message, 500


class NeutronUpdatePort(Resource):

    def __init__(self, api):
        self.api = api

    def put(self, port_id):
        logging.debug("API CALL: Neutron - Update port")
        try:
            for stack in self.api.compute.stacks.values():
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
                            port.set_name(port_dict["port"]["name"])
                            if port.net_name in stack.nets:
                                stack.nets[port.net_name].update_port_name_for_ip_address(port.ip_address, port.name)
                            stack.ports[port.name] = stack.ports[old_name]
                            del stack.ports[old_name]
                        if "network_id" in port_dict["port"]:
                            pass
                        if "status" in port_dict["port"]:
                            pass
                        if "tenant_id" in port_dict["port"]:
                            pass

                        tmp_port_dict = create_port_dict(port, self.api.compute)
                        tmp_dict = dict()
                        tmp_dict["port"] = tmp_port_dict

                        return Response(json.dumps(tmp_dict), status=200, mimetype='application/json')

            return 'Port not found.', 404

        except Exception as ex:
            logging.exception("Neutron: Update port exception.")
            return ex.message, 500


class NeutronDeletePort(Resource):

    def __init__(self, api):
        self.api = api

    def delete(self, port_id):
        logging.debug("API CALL: Neutron - Delete port")
        try:
            for stack in self.api.compute.stacks.values():
                for port in stack.ports.values():
                    if port.id == port_id:
                        port_name = port.name

                        if port.net_name in stack.nets:
                            stack.nets[port.net_name].withdraw_ip_address(port.ip_address)
                        for server in stack.servers.values():
                            try:
                                server.port_names.remove(port_name)
                            except ValueError:
                                pass

                        del stack.ports[port_name]

                        return 'Port ' + port_id + ' deleted.', 204

            return 'Could not find port.', 404

        except Exception as ex:
            logging.exception("Neutron: Delete port exception.")
            return ex.message, 500


def create_network_dict(network):
    network_dict = dict()
    network_dict["status"] = "ACTIVE"  # TODO do we support inactive networks?
    network_dict["subnets"] = [network.subnet_id]
    network_dict["name"] = network.name
    network_dict["admin_state_up"] = True  # TODO is it always true?
    network_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"  # TODO what should go in here
    network_dict["id"] = network.id
    network_dict["shared"] = False  # TODO is it always false?
    return network_dict


def create_subnet_dict(network):
    subnet_dict = dict()
    subnet_dict["name"] = network.subnet_name
    subnet_dict["network_id"] = network.id
    subnet_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"  # TODO what should go in here?
    subnet_dict["created_at"] = network.subnet_creation_time
    subnet_dict["dns_nameservers"] = []
    subnet_dict["allocation_pools"] = [network.start_end_dict]
    subnet_dict["host_routers"] = []
    subnet_dict["gateway_ip"] = network.gateway_ip
    subnet_dict["ip_version"] = "4"
    subnet_dict["cidr"] = network.get_cidr()
    subnet_dict["updated_at"] = network.subnet_update_time
    subnet_dict["id"] = network.subnet_id
    subnet_dict["enable_dhcp"] = False  # TODO do we support DHCP?
    return subnet_dict


def create_port_dict(port, compute):
    port_dict = dict()
    port_dict["admin_state_up"] = True  # TODO is it always true?
    port_dict["device_id"] = "257614cc-e178-4c92-9c61-3b28d40eca44"  # TODO find real values
    port_dict["device_owner"] = ""  # TODO do we have such things?
    tmp_subnet_id = None
    for stack in compute.stacks.values():
        if port.net_name in stack.nets:
            tmp_subnet_id = stack.nets[port.net_name].subnet_id
    tmp_ip_address = None
    if port.ip_address is not None:
        tmp_ip_address = port.ip_address.rsplit('/', 1)[0]
    port_dict["fixed_ips"] = [
                                  {
                                      "ip_address": tmp_ip_address,
                                      "subnet_id": tmp_subnet_id
                                  }
                             ]
    port_dict["id"] = port.id
    port_dict["mac_address"] = port.mac_address
    port_dict["name"] = port.name
    for stack in compute.stacks.values():
        if port.net_name in stack.nets:
            port_dict["network_id"] = stack.nets[port.net_name].id
        else:
            port_dict["network_id"] = None
    port_dict["status"] = "ACTIVE"  # TODO do we support inactive port?
    port_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"  # TODO find real tenant_id
    return port_dict


def create_link(net_name, compute):
    for stack in compute.stacks.values():
        for server in stack.servers.values():
            for port_name in server.port_names:  # TODO new ports are currently not added to any server.ports dict
                port = stack.ports[port_name]
                if port.net_name == net_name:
                    compute.dc.net.addLink(
                        compute.dc.containers[server.name],
                        compute.dc.switch,
                        params1={"ip": str(port.ip_address)},
                        cls=Link,
                        intfName1=net_name)
