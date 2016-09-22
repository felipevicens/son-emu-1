from __future__ import print_function  # TODO remove when print is no longer needed for debugging
import yaml
import sys
import uuid
from resources import *


class HeatParser:
    def __init__(self):
        self.description = None
        self.parameter_groups = None
        self.parameters = None
        self.resources = None
        self.outputs = None
        self.bufferResource = list()

    def parse_input(self, input_dict, stack, dc_label):
        if not (str(input_dict['heat_template_version']) == '2015-04-30'):  # TODO: change to versions equal or later then this date (to check that it is a HOT template)
            print('Unsupported template version: ' + input_dict['heat_template_version'], file=sys.stderr)
            return

        try:
            self.description = input_dict['description']
        except KeyError as e:
            self.description = None
            #print('No ' + e.message + ' found.')

        try:
            self.parameter_groups = input_dict['parameter_groups']
        except KeyError as e:
            self.parameter_groups = None
            #print('No ' + e.message + ' found.')

        try:
            self.parameters = input_dict['parameters']
        except KeyError as e:
            self.parameters = None
            #print('No ' + e.message + ' found.')

        try:
            self.resources = input_dict['resources']
        except KeyError as e:
            self.resources = None
            #print('No ' + e.message + ' found.')

        try:
            self.outputs = input_dict['outputs']
        except KeyError as e:
            self.outputs = None
            #print('No ' + e.message + ' found.')

        for resource in self.resources.values():
            self.handle_resource(resource, stack, dc_label)

        # This loop tries to create all classes which had unresolved dependencies.
        number_of_iterations = 5
        while len(self.bufferResource) > 0 and number_of_iterations > 0:
            number_of_iterations -= 1
            number_of_items = len(self.bufferResource)
            while number_of_items > 0:
                self.handle_resource(self.bufferResource.pop(0), stack, dc_label)
                number_of_items -= 1

        if len(self.bufferResource) > 0:
            print(str(len(self.bufferResource)) +
                  ' classes could not be created, because the dependencies could not be found.')

    def handle_resource(self, resource, stack, dc_label):   # TODO are all resource references complete?
        if "OS::Neutron::Net" in resource['type']:
            try:
                name = resource['properties']['name']
                if name not in stack.nets:
                    stack.nets[name] = Net(name)
                    stack.nets[name].id = str(uuid.uuid4())[:15]  # str(len(stack.nets)-1)

            except Exception as e:
                print('Could not create Net: ' + e.message)
            return

        if 'OS::Neutron::Subnet' in resource['type'] and "Net" not in resource['type']:
            try:
                net_name = resource['properties']['network']['get_resource']
                if net_name not in stack.nets:
                    stack.nets[net_name] = Net(net_name)
                    stack.nets[net_name].id = str(uuid.uuid4())[:15]  # str(len(stack.nets)-1)

                stack.nets[net_name].subnet_name = resource['properties']['name']
                if 'gateway_ip' in resource['properties']:
                    stack.nets[net_name].gateway_ip = resource['properties']['gateway_ip']
                stack.nets[net_name].subnet_id = stack.nets[net_name].id  # TODO could there be a different number of subnets than nets?
                stack.nets[net_name].set_cidr(resource['properties']['cidr'])
            except Exception as e:
                print('Could not create Subnet: ' + e.message)
            return

        if 'OS::Neutron::Port' in resource['type']:
            try:
                name = resource['properties']['name']
                if name not in stack.ports:
                    stack.ports[name] = Port(name)
                    stack.ports[name].id = str(uuid.uuid4())[:15]  # str(len(stack.ports)-1)

                for tmp_net in stack.nets.values():
                    if tmp_net.name == resource['properties']['network']['get_resource'] and \
                       tmp_net.subnet_id is not None:
                        stack.ports[name].net_id = tmp_net.id
                        stack.ports[name].ip_address = tmp_net.get_new_ip_address(name)
                        return
            except Exception as e:
                print('Could not create Port: ' + e.message)
            self.bufferResource.append(resource)
            return

        if 'OS::Nova::Server' in resource['type']:
            try:
                compute_name = str(dc_label) + '_' + str(stack.stack_name) + '_' + str(resource['properties']['name'])
                shortened_name = str(dc_label) + '_' + str(stack.stack_name) + '_' + \
                                 self.shorten_server_name(str(resource['properties']['name']), stack)
                nw_list = resource['properties']['networks']
                if shortened_name not in stack.servers:
                    stack.servers[shortened_name] = Server(shortened_name)

                stack.servers[shortened_name].full_name = compute_name
                stack.servers[shortened_name].command = '/bin/bash'
                stack.servers[shortened_name].image = resource['properties']['image']
                stack.servers[shortened_name].flavor = resource['properties']['flavor']
                for port in nw_list:
                    port_name = port['port']['get_resource']
                    if port_name not in stack.ports:
                        stack.ports[port_name] = Port(port_name)
                        stack.ports[port_name].id = str(uuid.uuid4())[:15]  # str(len(stack.ports)-1)

                    stack.servers[shortened_name].port_names.append(port_name)
            except Exception as e:
                print('Could not create Server: ' + e.message)
            return

        if 'OS::Neutron::RouterInterface' in resource['type']:
            try:
                router_name = None
                subnet_name = resource['properties']['subnet']['get_resource']

                if 'get_resource' in resource['properties']['router']:
                    router_name = resource['properties']['router']['get_resource']
                else:
                    router_name = resource['properties']['router']

                if router_name not in stack.routers:
                    stack.routers[router_name] = Router(router_name)

                for tmp_net in stack.nets.values():
                    if tmp_net.subnet_name == subnet_name:
                        stack.routers[router_name].add_subnet(tmp_net)
                        return
            except Exception as e:
                print('Could not create RouterInterface: ' + e.__repr__())
            self.bufferResource.append(resource)
            return

        if 'OS::Neutron::FloatingIP' in resource['type']:
            try:
                port_id = resource['properties']['port_id']['get_resource']
                floating_network_id = resource['properties']['floating_network_id']
                if port_id not in stack.ports:
                    stack.ports[port_id] = Port(port_id)
                    stack.ports[port_id].id = str(uuid.uuid4())[:15]  # str(len(stack.ports)-1)

                stack.ports[port_id].floating_ip = floating_network_id
            except Exception as e:
                print('Could not create FloatingIP: ' + e.message)
            return

        if 'OS::Neutron::Router' in resource['type']:
            try:
                name = resource['properties']['name']
                if name not in stack.routers:
                    stack.routers[name] = Router(name)
            except Exception as e:
                print('Could not create Router: ' + e.message)
            return

        print('Could not determine resource type!')
        return

    def shorten_server_name(self, server_name, stack):
        server_name = self.shorten_name(server_name, 12)
        iterator = 0
        while server_name in stack.servers:
            server_name = server_name[0:12] + str(iterator)
            iterator += 1
        return server_name

    def shorten_name(self, name, max_size):
        shortened_name = name.split(':', 1)[0]
        shortened_name = shortened_name.replace("-", "_")
        shortened_name = shortened_name[0:max_size]
        return shortened_name


if __name__ == '__main__':
    inputFile = open('yamlTest2', 'r')
    inp = inputFile.read()
    inputFile.close()
    stack = Stack()
    x = HeatParser()
    x.parse_input(inp, stack)
