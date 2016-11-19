import re

class Net:
    def __init__(self, name):
        self.name = name
        self.id = id
        self.subnet_name = None
        self.subnet_id = None
        self.subnet_creation_time = None
        self.subnet_update_time = None
        self.gateway_ip = None
        self.segmentation_id = None  # not set
        self._cidr = None
        self.start_end_dict = None
        self._issued_ip_addresses = dict()

    def get_short_id(self):
        return str(self.id)[:6]

    def get_new_ip_address(self, port_name):
        if self.start_end_dict is None:
            return None

        int_start_ip = self.ip_2_int(self.start_end_dict['start']) + 2  # First address as network address not usable
                                                                        # Second one is for gateways only
        int_end_ip = self.ip_2_int(self.start_end_dict['end']) - 1      # Last address for broadcasts
        while int_start_ip in self._issued_ip_addresses and int_start_ip <= int_end_ip:
            int_start_ip+=1

        if int_start_ip > int_end_ip:
            return None

        self._issued_ip_addresses[int_start_ip] = port_name
        return self.int_2_ip(int_start_ip) + '/' + self._cidr.rsplit('/', 1)[1]

    def get_in_ip_address(self, port_name):
        int_start_ip = self.ip_2_int(self.start_end_dict['start']) + 2
        self._issued_ip_addresses[int_start_ip] = port_name
        return self.int_2_ip(int_start_ip) + '/' + self._cidr.rsplit('/', 1)[1]

    def get_out_ip_address(self, port_name):
        int_start_ip = self.ip_2_int(self.start_end_dict['start']) + 3
        self._issued_ip_addresses[int_start_ip] = port_name
        return self.int_2_ip(int_start_ip) + '/' + self._cidr.rsplit('/', 1)[1]

    def withdraw_ip_address(self, ip_address):
        address, suffix = ip_address.rsplit('/', 1)
        int_ip_address = self.ip_2_int(address)
        del self._issued_ip_addresses[int_ip_address]

    def reset_issued_ip_addresses(self):
        self._issued_ip_addresses = dict()

    def update_port_name_for_ip_address(self, ip_address, port_name):
        address, suffix = ip_address.rsplit('/', 1)
        int_ip_address = self.ip_2_int(address)
        self._issued_ip_addresses[int_ip_address] = port_name

    def set_cidr(self, cidr):
        if cidr is None:
            self._cidr = None
            return True
        if not self.check_cidr_format(cidr):
            return False

        if len(self._issued_ip_addresses) > 0:
            self.reset_issued_ip_addresses()
        self.start_end_dict = self.calculate_start_and_end_dict(cidr)
        self._cidr = cidr
        return True

    def get_cidr(self):
        return self._cidr

    def calculate_start_and_end_dict(self, cidr):
        address, suffix = cidr.rsplit('/', 1)
        int_suffix = int(suffix)
        int_address = self.ip_2_int(address)
        address_space = 2 ** 32 - 1

        for x in range(0, 31 - int_suffix):
            address_space = ~(~address_space | (1 << x))

        start = int_address & address_space
        end = start + (2 ** (32 - int_suffix) - 1)

        return {'start': self.int_2_ip(start), 'end': self.int_2_ip(end)}

    def ip_2_int(self, ip):
        o = map(int, ip.split('.'))
        res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
        return res

    def int_2_ip(self, int_ip):
        o1 = int(int_ip / 16777216) % 256
        o2 = int(int_ip / 65536) % 256
        o3 = int(int_ip / 256) % 256
        o4 = int(int_ip) % 256
        return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()

    def check_cidr_format(self, cidr):
        r = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{2}')
        if r.match(cidr):
            return True
        return False

    def create_network_dict(self):
        network_dict = dict()
        network_dict["status"] = "ACTIVE"  # TODO do we support inactive networks?
        network_dict["subnets"] = [self.subnet_id]
        network_dict["name"] = self.name
        network_dict["admin_state_up"] = True  # TODO is it always true?
        network_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"  # TODO what should go in here
        network_dict["id"] = self.id
        network_dict["shared"] = False  # TODO is it always false?
        return network_dict

    def create_subnet_dict(self):
        subnet_dict = dict()
        subnet_dict["name"] = self.subnet_name
        subnet_dict["network_id"] = self.id
        subnet_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"  # TODO what should go in here?
        subnet_dict["created_at"] = self.subnet_creation_time
        subnet_dict["dns_nameservers"] = []
        subnet_dict["allocation_pools"] = [self.start_end_dict]
        subnet_dict["host_routers"] = []
        subnet_dict["gateway_ip"] = self.gateway_ip
        subnet_dict["ip_version"] = "4"
        subnet_dict["cidr"] = self.get_cidr()
        subnet_dict["updated_at"] = self.subnet_update_time
        subnet_dict["id"] = self.subnet_id
        subnet_dict["enable_dhcp"] = False  # TODO do we support DHCP?
        return subnet_dict

    def __eq__(self, other):
        if self.name == other.name and self.subnet_name == other.subnet_name and \
                                       self.gateway_ip == other.gateway_ip and \
                                       self.segmentation_id == other.segmentation_id and \
                                       self._cidr == other._cidr and \
                                       self.start_end_dict == other.start_end_dict:
            return True
        return False

    def __hash__(self):
        return hash((self.name,
                     self.subnet_name,
                     self.gateway_ip,
                     self.segmentation_id,
                     self._cidr,
                     self.start_end_dict))
