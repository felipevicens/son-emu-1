
class Server:
    def __init__(self,name, id=None, flavor=None, image=None, command=None, nw_list=None):
        self.name = name
        self.full_name = None
        self.id = id          # not set
        self.flavor = flavor
        self.image = image
        self.command = command
        self.port_names = list()

    def compare_attributes(self, other):
        if self.name == other.name and self.full_name == other.full_name and \
                                       self.flavor == other.flavor and \
                                       self.image == other.image and \
                                       self.command == other.command:
            return True
        return False

    def __eq__(self, other):
        if self.name == other.name and self.full_name == other.full_name and\
                                       self.flavor == other.flavor and \
                                       self.image == other.image and \
                                       self.command == other.command and \
                                       len(self.port_names) == len(other.port_names) and \
                                       set(self.port_names) == set(other.port_names):
            return True
        return False
