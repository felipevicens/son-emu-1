from resources import *
from mininet.link import Link
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

        # Update Stack IDs
        for server in old_stack.servers.values():
            if server.name in new_stack.servers:
                new_stack.servers[server.name].id = server.id
        for net in old_stack.nets.values():
            if net.name in new_stack.nets:
                new_stack.nets[net.name].id = net.id
        for port in old_stack.ports.values():
            if port.name in new_stack.ports:
                new_stack.ports[port.name].id = port.id
        for router in old_stack.routers.values():
            if router.name in new_stack.routers:
                new_stack.routers[router.name].id = router.id

        # Remove all unnecessary servers
        for server in old_stack.servers.values():
            if server.name in new_stack.servers:
                if not server.compare_attributes(new_stack.servers[server.name]):
                    self._stop_compute(server, old_stack)
                else:
                    # Delete unused and changed links
                    for port_name in server.port_names:
                        if port_name in new_stack.ports:
                            if not old_stack.ports[port_name] == new_stack.ports[port_name]:
                                my_links = self.dc.net.links
                                for link in my_links:
                                    net_short_id, port_short_id = str(link.intf1).split('-', 1)
                                    tmp_net = old_stack.nets[old_stack.ports[port_name].net_name]
                                    if old_stack.ports[port_name].get_short_id() == port_short_id and \
                                       tmp_net.get_short_id() == net_short_id:
                                        self.dc.net.removeLink(link=link)

                                        # Add changed link
                                        tmp_net = new_stack.nets[new_stack.ports[port_name].net_name]
                                        self._add_link(server.name,
                                                       self.dc.name + '.s1',
                                                       new_stack.ports[port_name].ip_address,
                                                       str(tmp_net.get_short_id()) +
                                                       '-' + str(new_stack.ports[port_name].get_short_id()))
                                        break
                        else:
                            my_links = self.dc.net.links
                            for link in my_links:
                                net_short_id, port_short_id = str(link.intf1).split('-', 1)
                                tmp_net = old_stack.nets[old_stack.ports[port_name].net_name]
                                if old_stack.ports[port_name].get_short_id() == port_short_id and \
                                   tmp_net.get_short_id() == net_short_id:
                                    self.dc.net.removeLink(link=link)

                    # Create new links
                    for port_name in new_stack.servers[server.name].port_names:
                        if port_name not in server.port_names:
                            self._add_link(server.name,
                                           self.dc.name + '.s1',
                                           new_stack.ports[port_name].ip_address,
                                           str(new_stack.nets[new_stack.ports[port_name].net_name].get_short_id()) +
                                           '-' + str(new_stack.ports[port_name].get_short_id()))
            else:
                self._stop_compute(server, old_stack)

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
        for port_name in server.port_names:
            network_dict = dict()
            network_dict['id'] = str(stack.nets[stack.ports[port_name].net_name].get_short_id()) + \
                                 '-' + str(stack.ports[port_name].get_short_id())
            network_dict['ip'] = stack.ports[port_name].ip_address
            network.append(network_dict)

        c = self.dc.startCompute(server.name, image=server.image, command=server.command, network=network)

    def _stop_compute(self, server, stack):
        link_names = list()
        for port_name in server.port_names:
            link_names.append(str(stack.nets[stack.ports[port_name].net_name].get_short_id() +
                                  '-' + stack.ports[port_name].get_short_id()))
        my_links = self.dc.net.links
        for link in my_links:
            if str(link.intf1) in link_names:
                self.dc.net.removeLink(link=link)
        self.dc.stopCompute(server.name)

    def _add_link(self, node_name, switch_name, ip_address, link_name):
        node = self.dc.net.get(node_name)
        switch = self.dc.net.get(switch_name)
        nw = {'ip': ip_address,
              'id': link_name}
        self.dc.net.addLink(node, switch, params1=nw, cls=Link, intfName1=link_name)
