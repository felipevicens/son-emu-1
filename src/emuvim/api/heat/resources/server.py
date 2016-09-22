
class Server:
    def __init__(self,name, id=None, flavor=None, image=None, command=None, nw_list=None):
        self.name = name
        self.full_name = None
        self.id = id          # not set
        self.flavor = flavor
        self.image = image
        self.command = command
        self.port_names = list()

    def __eq__(self, other):
        if self.name == other.name and self.full_name == other.full_name and\
                                       self.flavor == other.flavor and \
                                       self.image == other.image and \
                                       self.command == other.command and \
                                       len(self.port_names) == len(other.ports) and \
                                       set(self.port_names) == set(other.ports):
            return True
        return False
