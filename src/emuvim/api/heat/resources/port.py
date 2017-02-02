import logging
import threading

lock = threading.Lock()
intf_names = {}


class Port:
    def __init__(self, name, ip_address=None, mac_address=None, floating_ip=None):
        self.name = name
        self.intf_name = None
        self.__create_intf_name()
        self.id = None
        self.template_name = name
        self.ip_address = ip_address
        self.mac_address = mac_address  # not set
        self.floating_ip = floating_ip
        self.net_name = None

    def set_name(self, name):
        """
        Sets the port name.

        :param name: New port name.
        :type name: ``str``
        """
        if self.name == name:
            return

        # Delete old interface name
        global lock
        lock.acquire()
        if intf_names[self.intf_name] == self.name:
            del intf_names[self.intf_name]
        lock.release()

        self.name = name
        # Create new interface name
        self.__create_intf_name()

    def __create_intf_name(self):
        """
        Creates the interface name, while using the first 4 letters of the port name, the specification, if it is an
        'in' / 'out' port or something else, and a counter value if the name is already used. The counter starts
        for each name at 0 and can go up to 999. After creating the name each port will post its interface name
        into the global dictionary and adding his full name. Thus each port can determine if his desired interface
        name is already used and choose the next one.
        """
        split_name = self.name.split(':')
        if len(split_name) >= 3:
            if split_name[2] == 'input' or split_name[2] == 'in':
                self.intf_name = split_name[0][:4] + '-' + \
                                 'in'
            elif split_name[2] == 'output' or split_name[2] == 'out':
                self.intf_name = split_name[0][:4] + '-' + \
                                 'out'
            else:
                self.intf_name = split_name[0][:4] + '-' + \
                                 split_name[2][:4]
        else:
            self.intf_name = self.name[:9]

        global lock
        lock.acquire()
        counter = 0
        global intf_names
        intf_len = len(self.intf_name)
        self.intf_name = self.intf_name + '-' + str(counter)[:4]
        while self.intf_name in intf_names and counter < 999:
            counter += 1
            self.intf_name = self.intf_name[:intf_len] + '-' + str(counter)[:4]

        if counter >= 1000:
            logging.ERROR("Port %s could not create unique interface name (%s)", self.name, self.intf_name)
            lock.release()
            return

        intf_names[self.intf_name] = self.name
        lock.release()

    def update_intf_name(self, new_intf_name):
        """
        The port interface name will be set to the give name, if it is not used yet or if the dictionary entry for
        the new interface name contains the name of the port (this will occur if a stack will be updated and the
        old stack also contains the same connection).

        :param new_intf_name: The new interface name.
        :type new_intf_name: ``str``
        :return: * *True*: If the interface name is now the new interface name.
            * *False*: If the new interface name is already used.
        :rtype: ``bool``
        """
        if self.intf_name == new_intf_name:
            return True

        global lock
        lock.acquire()
        global intf_names
        ok = False
        if intf_names.get(new_intf_name) == None:
            ok = True
        elif intf_names[new_intf_name] == self.name:
            ok = True

        if ok:
            intf_names[new_intf_name] = self.name
            if intf_names[self.intf_name] == self.name:
                del intf_names[self.intf_name]
            self.intf_name = new_intf_name
        lock.release()
        return ok

    def get_short_id(self):
        """
        Gets a shortened ID which only contains first 6 characters.

        :return: The first 6 characters of the UUID.
        :rtype: ``str``
        """
        return str(self.id)[:6]

    def create_port_dict(self, compute):
        """
        Creates the port description dictionary.

        :param compute: Requires the compute resource to determine the used network.
        :type compute: :class:`heat.compute`
        :return: Returns the description dictionary.
        :rtype: ``dict``
        """
        port_dict = dict()
        port_dict["admin_state_up"] = True  # TODO is it always true?
        port_dict["device_id"] = "257614cc-e178-4c92-9c61-3b28d40eca44"  # TODO find real values
        port_dict["device_owner"] = ""  # TODO do we have such things?
        net = compute.find_network_by_name_or_id(self.net_name)
        port_dict["fixed_ips"] = [
            {
                "ip_address": self.ip_address.rsplit('/', 1)[0] if self.ip_address is not None else "",
                "subnet_id": net.subnet_id if net is not None else ""
            }
        ]
        port_dict["id"] = self.id
        port_dict["mac_address"] = self.mac_address
        port_dict["name"] = self.name
        port_dict["network_id"] = net.id if net is not None else ""
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

    def __del__(self):
        global lock
        lock.acquire()
        global intf_names
        if self.intf_name in intf_names and intf_names[self.intf_name] == self.name:
            del intf_names[self.intf_name]
        lock.release()
