
class Port:
    def __init__(self, name, ip_address=None, mac_address=None, floating_ip=None):
        self.name = name
        self.id = None
        self.ip_address = ip_address    # not set
        self.mac_address = mac_address  # not set
        self.floating_ip = floating_ip
        self.net = None
