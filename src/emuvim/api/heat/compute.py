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
        self.networks = list()

    def add_stack(self, stack):
        self.check_stack(stack)
        self.stacks[stack.id] = stack

    def add_network(self, network):
        self.networks.append(network)


    #TODO check the stack
    def check_stack(self, stack):
        #raise HeatApiStackInvalidException("Stack did not pass validity checks")
        return True

    def deploy_stack(self, stackid):
        if self.dc is None:
            return False

        stack = self.stacks[stackid]

        #Create the networks first
        id = 0
        for net in stack.nets.values():
            net.id = str(id)       # just added ids TODO maybe change the id to something else
            id += 1

        for server in stack.servers.values():
            logging.debug("Starting new compute resources %s" % server.name)
            network = list()
            for port in server.ports:
                network_dict = dict()
                network_dict['id'] = port.net.id
                network_dict['ip'] = port.net.cidr
                network.append(network_dict)

            c = self.dc.startCompute(server.name, image=server.image, command=server.command, network=network)

        logging.info(stack.servers)

