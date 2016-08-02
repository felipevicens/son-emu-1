
class Router:
    def __init__(self, name, id=None):
        self.name = name
        self.id = id
        self.subnet = list()

    def add_subnet(self, subnet):
        self.subnet.append(subnet)
