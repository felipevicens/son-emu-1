class Net:
    def __init__(self, name, id=None, subnet_name=None, subnet_id=None, segmentation_id=None, cidr=None):
        self.name = name
        self.id = id
        self.subnet_name = subnet_name
        self.subnet_id = subnet_id              # maybe wrong set
        self.segmentation_id = segmentation_id  # not set
        self.cidr = cidr