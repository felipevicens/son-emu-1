import uuid

class Stack:
    def __init__(self, id=None):
        self.servers = dict()
        self.server_names = dict()
        self.nets = dict()
        self.ports = dict()
        self.routers = dict()
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

    def add_server(self, server):
        self.servers[server.name] = server

    def add_net(self, net):
        self.nets[net.name] = net

    def add_port(self, port):
        self.ports[port.name] = port

    def add_router(self, router):
        self.routers[router.name] = router
