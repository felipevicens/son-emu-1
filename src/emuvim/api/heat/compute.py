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
            logging.debug("Starting new compute resources %s" % server.name)
            network = list()
            for port in server.ports:
                network_dict = dict()
                network_dict['id'] = port.net.id
                network_dict['ip'] = port.net.cidr
                network.append(network_dict)

            c = self.dc.startCompute(server.name, image=server.image, command=server.command, network=network)

    def delete_stack(self, stack_id):
        if self.dc is None:
            return False

        stack = self.stacks[stack_id]
        for server in stack.servers.values():
            self.dc.stopCompute(server.name)

        del self.stacks[stack_id]
