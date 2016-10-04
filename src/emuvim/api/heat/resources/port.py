
class Port:
    def __init__(self, name, ip_address=None, mac_address=None, floating_ip=None):
        self.name = name
        self.id = None
        self.ip_address = ip_address
        self.mac_address = mac_address  # not set
        self.floating_ip = floating_ip
        self.net_name = None

    def get_short_id(self):
        return str(self.id)[:6]

    def __eq__(self, other):
        if self.name == other.name and self.ip_address == other.ip_address and \
                                       self.mac_address == other.mac_address and \
                                       self.floating_ip == other.floating_ip and \
                                       self.net_name == other.net_name:
            return True
        return False

    def __hash__(self):
        return hash((self.name,
                     self.ip_address,
                     self.mac_address,
                     self.floating_ip,
                     self.net_name))
