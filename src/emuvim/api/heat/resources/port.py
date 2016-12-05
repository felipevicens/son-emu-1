
class Port:
    def __init__(self, name, ip_address=None, mac_address=None, floating_ip=None):
        self.name = None
        self.set_name(name)
        self.id = None
        self.template_name = name
        self.ip_address = ip_address
        self.mac_address = mac_address  # not set
        self.floating_ip = floating_ip
        self.net_name = None

    def set_name(self, name):
        self.name = name
        split_name = name.split(':')
        if len(split_name) >= 3:
            if split_name[2] == 'input' or split_name[2] == 'in':
                self.intf_name = split_name[0][:4] + '-' + \
                                 split_name[1][:4] + '-' + \
                                 'in'
            elif split_name[2] == 'output' or split_name[2] == 'out':
                self.intf_name = split_name[0][:4] + '-' + \
                                 split_name[1][:4] + '-' + \
                                 'out'
            else:
                self.intf_name = split_name[0][:4] + '-' + \
                                 split_name[1][:4] + '-' + \
                                 split_name[2][:4]
        else:
            self.intf_name = name

    def get_short_id(self):
        return str(self.id)[:6]

    def create_port_dict(self, compute):
        port_dict = dict()
        port_dict["admin_state_up"] = True  # TODO is it always true?
        port_dict["device_id"] = "257614cc-e178-4c92-9c61-3b28d40eca44"  # TODO find real values
        port_dict["device_owner"] = ""  # TODO do we have such things?
        net = compute.find_network_by_name_or_id(self.net_name)
        port_dict["fixed_ips"] = [
            {
                "ip_address": self.ip_address.rsplit('/', 1)[0] if self.ip_address is not None else None,
                "subnet_id": net.subnet_id if net is not None else None
            }
        ]
        port_dict["id"] = self.id
        port_dict["mac_address"] = self.mac_address
        port_dict["name"] = self.name
        port_dict["network_id"] = net.id if net is not None else None
        port_dict["status"] = "ACTIVE"  # TODO do we support inactive port?
        port_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"  # TODO find real tenant_id
        return port_dict

    def __eq__(self, other):
        if other is None:
            return False

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
