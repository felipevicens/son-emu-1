
class Router:
    def __init__(self, name, id=None):
        self.name = name
        self.id = id
        self.subnet = list()

    def add_subnet(self, subnet):
        self.subnet.append(subnet)

    def __eq__(self, other):
        if self.name == other.name and len(self.subnet) == len(other.subnet) and \
                                       set(self.subnet) == set(other.subnet):
            return True
        return False
