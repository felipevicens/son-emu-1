from resources import *
import logging

logging.basicConfig(level=logging.DEBUG)

class HeatApiStackInvalidException(BaseException):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)

class HeatCompute:
    def __init__(self):
        self.dc = None
        self.stacks = dict()
        self.computeUnits = dict()
        self.routers = dict()

    def add_stack(self, stack):
        self.check_stack(stack)
        self.stacks[stack.id] = stack


    #TODO check the stack
    def check_stack(self, stack):
        #raise HeatApiStackInvalidException("Stack did not pass validity checks")
        return True

    def deploy_stack(self, stackid):
        if self.dc is None:
            return False

        stack = self.stacks[stackid]

        #Create the networks first

        for net in stack.nets:


        for server in stack.servers:
            logging.debug("Starting new compute resources %s" % server.name)
            c = self.dc.startCompute(
                server.name, image=server.image, command=server.command, network=server.nw_list.first())

        logging.info(stack.servers)

