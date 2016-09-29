from resources import *
from mininet.link import Link
import logging
import hashlib

logging.basicConfig(level=logging.DEBUG)

SWITCH_ID = 0

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

        # Start the servers first
        for server in stack.servers.values():
            self._start_server(server)
            #self._start_compute(server, stack)

        # Then create the network
        self._create_network(stack)

    def delete_stack(self, stack_id):
        if self.dc is None:
            return False

        tmp_links = list(self.dc.net.links)
        for link in tmp_links:
            self.dc.net.removeLink(link=link)

        stack = self.stacks[stack_id]
        for server in stack.servers.values():
            self._stop_server(server.name)

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

                self._stop_server(server.name)

        # Remove all unused routers
        for router in old_stack.routers.values():
            if not (router.name in new_stack.routers and router == new_stack.routers[router.name]):
                my_links = self.dc.net.links
                for link in my_links:
                    if link.intf1.node == self.dc.net.get(router.get_short_id()) or \
                       link.intf2.node == self.dc.net.get(router.get_short_id()):
                        self.dc.net.removeLink(link)
            else:
                new_stack.routers[router.name].id = router.id

        # Start all new routers
        for router in new_stack.routers.values():
            try:
                if self.dc.net.get(router.get_short_id()) is not None:
                    print(self.dc.net.get(router.get_short_id()))
                    self._add_switch(router.get_short_id())
            except Exception as ex:
                print('Could not create router with name: ' + router.get_short_id())
                print(ex.message)

        # Start all new servers
        for server in new_stack.servers.values():
            if server.name not in self.dc.containers:
                #self._start_compute(server, new_stack)
                self._start_server(server)
                self._create_network_for_server(server, new_stack)

        del self.stacks[old_stack_id]
        self.stacks[new_stack.id] = new_stack
        return True

    def _start_server(self, server):
        d = self.dc.net.addDocker("%s" % (server.name),
                                  dimage=server.image,
                                  dcmd=server.command,
                                  datacenter=self.dc,
                                  flavor_name=server.flavor)
        self.dc.containers[server.name] = d

    def _stop_server(self, server_name):
        self.dc.net.removeDocker("%s" % (server_name))
        del self.dc.containers[server_name]

    def _create_network(self, stack):
        """
        First start the servers - otherwise we cannot connect links between switches and servers.
        :param stack:
        :return:
        """
        for router in stack.routers.values():
            self._add_switch(router.get_short_id())

        for port in stack.ports.values():
            for net in stack.nets.values():
                if net.id == port.net_id:
                    for server in stack.servers.values():
                        for port_name in server.port_names:
                            if port.name == port_name:
                                for router in stack.routers.values():
                                    for subnet_name in router.subnet_names:
                                        if net.subnet_name == subnet_name:
                                            self._add_link(server.name,
                                                           router.get_short_id(),
                                                           port.ip_address)

    def _create_network_for_server(self, server, stack):
        """
        All routers have to be created at this point!
        :param server:
        :return:
        """

        for port_name in server.port_names:
            for port in stack.ports.values():
                if port.name == port_name:
                    for router in stack.routers.values():
                        for subnet_name in router.subnet_names:
                            if net.subnet_name == subnet_name:
                                self._add_link(server.name,
                                               router.get_short_id(),
                                               port.ip_address)

    def _start_compute(self, server, stack):  # deprecated
        logging.debug("Starting new compute resources %s" % server.name)
        network = list()
        for port_name in server.port_names:
            network_dict = dict()
            network_dict['id'] = stack.ports[port_name].net_id
            network_dict['ip'] = stack.ports[port_name].ip_address
            network.append(network_dict)

        c = self.dc.startCompute(server.name, image=server.image, command=server.command, network=network)

    def _add_switch(self, name):
        global SWITCH_ID
        SWITCH_ID += 1
        self.dc.net.addSwitch(name, dpid=hex(SWITCH_ID))

    def _add_link(self, node_name, switch_name, ip_address):
        node = self.dc.net.get(node_name)
        switch = self.dc.net.get(switch_name)
        link_name = self.short_hash((node_name, switch_name))
        nw = {'ip': ip_address,
              'id': link_name}
        self.dc.net.addLink(node, switch, params1=nw, cls=Link, intfName1=link_name)

    def short_hash(self, name):
        return hex(abs(hash(name)))[2:10]