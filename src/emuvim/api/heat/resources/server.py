
class Server:
    def __init__(self,name, id=None, flavor=None, image=None, command=None, nw_list=None):
        self.name = name
        self.id = id          # not set
        self.flavor = flavor
        self.image = image
        self.command = command
        self.ports = list()

    def __eq__(self, other):
        if self.name == other.name and self.flavor == other.flavor and \
                                       self.image == other.image and \
                                       self.command == other.command and \
                                       len(self.ports) == len(other.ports) and \
                                       set(self.ports) == set(other.ports):
            return True
        return False
