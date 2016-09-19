class Net:
    def __init__(self, name, id=None, subnet_name=None, subnet_id=None, segmentation_id=None, cidr=None):
        self.name = name
        self.id = id                            # currently only a consecutively numbered
        self.subnet_name = subnet_name
        self.subnet_id = subnet_id
        self.gateway_ip = None
        self.segmentation_id = segmentation_id  # not set
        self.cidr = cidr

    def __eq__(self, other):
        if self.name == other.name and self.subnet_name == other.subnet_name and \
                                       self.gateway_ip == other.gateway_ip and \
                                       self.segmentation_id == other.segmentation_id and \
                                       self.cidr == other.cidr:
            return True
        return False

    def __hash__(self):
        return hash((self.name,
                     self.subnet_name,
                     self.gateway_ip,
                     self.segmentation_id,
                     self.cidr))
