from resources import *
import logging

logging.basicConfig(level=logging.DEBUG)


class HeatApiStackInvalidException(BaseException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class OpenstackCompute:
    def __init__(self):
        self.dc = None
        self.stacks = dict()
        self.computeUnits = dict()
        self.routers = dict()
        self.flavors = dict()

    def add_stack(self, stack):
        self.check_stack(stack)
        self.stacks[stack.id] = stack

    # TODO check the stack
    def check_stack(self, stack):
        # raise HeatApiStackInvalidException("Stack did not pass validity checks")
        return True

    def add_flavor(self, name, cpu, memory, memory_unit, storage, storage_unit):
        flavor = InstanceFlavor(name, cpu, memory, memory_unit, storage, storage_unit )
        self.flavors[flavor.id] = flavor

    def deploy_stack(self, stackid):
        if self.dc is None:
            return False

        stack = self.stacks[stackid]

        # Create the networks first
        for server in stack.servers.values():
            self._start_compute(server, stack)

    def delete_stack(self, stack_id):
        if self.dc is None:
            return False

        tmp_links = list(self.dc.net.links)
        for link in tmp_links:
            self.dc.net.removeLink(link=link)

        stack = self.stacks[stack_id]
        for server in stack.servers.values():
            self.dc.stopCompute(server.name)

        del self.stacks[stack_id]

    def update_stack(self, old_stack_id, new_stack):
        if old_stack_id in self.stacks:
            old_stack = self.stacks[old_stack_id]
        else:
            return False

        # Remove all unnecessary servers
        for server in old_stack.servers.values():
            if not (server.name in new_stack.servers and server == new_stack.servers[server.name]):
                my_links = self.dc.net.links
                for link in my_links:
                    if link.intf1.node == self.dc.net.get(server.name) or \
                       link.intf2.node == self.dc.net.get(server.name):
                        self.dc.net.removeLink(link)

                self.dc.stopCompute(server.name)

        # Start all new servers
        for server in new_stack.servers.values():
            if server.name not in self.dc.containers:
                self._start_compute(server, new_stack)

        del self.stacks[old_stack_id]
        self.stacks[new_stack.id] = new_stack
        return True

    def _start_compute(self, server, stack):
        logging.debug("Starting new compute resources %s" % server.name)
        network = list()
        for port_name in server.ports:
            network_dict = dict()
            network_dict['id'] = stack.ports[port_name].net_id
            network_dict['ip'] = stack.ports[port_name].ip_address
            network.append(network_dict)

        c = self.dc.startCompute(server.name, image=server.image, command=server.command, network=network)
