import uuid

class Stack:
    def __init__(self, id=None):
        self.servers = dict()
        self.nets = dict()
        self.ports = dict()
        self.routers = dict()
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

    def add_server(self, server):
        self.servers.append(server)

    def add_net(self, net):
        self.nets.append(net)

    def add_port(self, port):
        self.ports.append(port)

    def add_router(self, router):
        self.routers.append(router)