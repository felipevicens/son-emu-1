class Net:
    def __init__(self, name, id=None, subnet_name=None, subnet_id=None, segmentation_id=None, cidr=None):
        self.name = name
        self.id = id                            # currently only a consecutively numbered
        self.subnet_name = subnet_name
        self.subnet_id = subnet_id
        self.gateway_ip = None
        self.segmentation_id = segmentation_id  # not set
        self.cidr = cidr
