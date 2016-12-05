from mininet.link import Link
from resources import *
from docker import Client
from docker.utils import kwargs_from_env
import logging
import threading
import time
import re
import uuid


class HeatApiStackInvalidException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class OpenstackCompute(object):
    def __init__(self):
        self.dc = None
        self.stacks = dict()
        self.computeUnits = dict()
        self.routers = dict()
        self.flavors = dict()
        self._images = dict()
        self.nets = dict()
        self.ports = dict()
        self.compute_nets = dict()
        self.dcli = Client(base_url='unix://var/run/docker.sock')

    @property
    def images(self):
        # update the known images. ask the docker daemon for a list of all known images
        for image in self.dcli.images():
            if 'RepoTags' in image:
                found = False
                imageName = image['RepoTags']
                if imageName == None:
                    continue
                imageName = imageName[0]
                for i in self._images.values():
                    if i.name == imageName:
                        found = True
                        break
                if not found:
                    self._images[imageName] = Image(imageName)
        return self._images

    def add_stack(self, stack):
        if not self.check_stack(stack):
            raise HeatApiStackInvalidException("Stack did not pass validity checks")
        self.stacks[stack.id] = stack

    def check_stack(self, stack):
        """
        Checks all dependencies of all servers, ports and routers and their most important parameters.
        :param stack: A reference of the stack that should be checked.
        :return: True: if the stack is completely fine. - False: else
        """
        everything_ok = True
        for server in stack.servers.values():
            for port_name in server.port_names:
                if port_name not in stack.ports:
                    logging.warning("Server %s of stack %s has a port named %s that is not known." %
                                    (server.name, stack.stack_name, port_name))
                    everything_ok = False
            if server.image is None:
                logging.warning("Server %s holds no image." % (server.name))
                everything_ok = False
            if server.command is None:
                logging.warning("Server %s holds no command." % (server.name))
                everything_ok = False
        for port in stack.ports.values():
            if port.net_name not in stack.nets:
                logging.warning("Port %s of stack %s has a network named %s that is not known." %
                                (port.name, stack.stack_name, port.net_name))
                everything_ok = False
            if port.intf_name is None:
                logging.warning("Port %s has no interface name." % (port.name))
                everything_ok = False
            if port.ip_address is None:
                logging.warning("Port %s has no IP address." % (port.name))
                everything_ok = False
        for router in stack.routers.values():
            for subnet_name in router.subnet_names:
                found = False
                for net in stack.nets.values():
                    if net.subnet_name == subnet_name:
                        found = True
                        break
                if not found:
                    logging.warning("Router %s of stack %s has a network named %s that is not known." %
                                    (router.name, stack.stack_name, subnet_name))
                    everything_ok = False
        return everything_ok

    def add_flavor(self, name, cpu, memory, memory_unit, storage, storage_unit):
        flavor = InstanceFlavor(name, cpu, memory, memory_unit, storage, storage_unit)
        self.flavors[flavor.name] = flavor

    def deploy_stack(self, stackid):
        if self.dc is None:
            return False

        stack = self.stacks[stackid]

        # Create the networks first
        for server in stack.servers.values():
            self._start_compute(server, stack)

    def delete_stack(self, stack_id):
        if self.dc is None:
            return False

        # Stop all servers and their links of this stack
        for server in self.stacks[stack_id].servers.values():
            self._stop_compute(server)
            self.delete_server(server.id)
        for net in self.stacks[stack_id].nets.values():
            self.delete_network(net.id)
        for port in self.stacks[stack_id].ports.values():
            self.delete_port(port.id)

        del self.stacks[stack_id]

    def update_stack(self, old_stack_id, new_stack):
        """
        Determines differences within the old and the new stack and deletes, create or changes only parts that
        differ between the two stacks.
        :param old_stack_id: The ID of the old stack.
        :param new_stack: A reference of the new stack.
        :return: True: if the old stack could be updated to the new stack without any error. - False: else
        """
        if old_stack_id not in self.stacks:
            return False
        old_stack = self.stacks[old_stack_id]

        if not self.check_stack(new_stack):
            return False

        # Update Stack IDs
        for server in old_stack.servers.values():
            if server.name in new_stack.servers:
                new_stack.servers[server.name].id = server.id
        for net in old_stack.nets.values():
            if net.name in new_stack.nets:
                new_stack.nets[net.name].id = net.id
                for subnet in new_stack.nets.values():
                    if subnet.subnet_name == net.subnet_name:
                        subnet.subnet_id = net.subnet_id
                        break
            else:
                self.delete_network(net.id)
        for port in old_stack.ports.values():
            if port.name in new_stack.ports:
                new_stack.ports[port.name].id = port.id
        for router in old_stack.routers.values():
            if router.name in new_stack.routers:
                new_stack.routers[router.name].id = router.id

        # Remove all unnecessary servers
        for server in old_stack.servers.values():
            if server.name in new_stack.servers:
                if not server.compare_attributes(new_stack.servers[server.name]):
                    self._stop_compute(server)
                else:
                    # Delete unused and changed links
                    for port_name in server.port_names:
                        if port_name in old_stack.ports and port_name in new_stack.ports:
                            if not old_stack.ports.get(port_name) == new_stack.ports.get(port_name):
                                my_links = self.dc.net.links
                                for link in my_links:
                                    if str(link.intf1) == old_stack.ports[port_name].intf_name and \
                                                    str(link.intf1.ip) == \
                                                    old_stack.ports[port_name].ip_address.split('/')[0]:
                                        self._remove_link(server.name, link)

                                        # Add changed link
                                        self._add_link(server.name,
                                                       new_stack.ports[port_name].ip_address,
                                                       new_stack.ports[port_name].intf_name,
                                                       new_stack.ports[port_name].net_name)
                                        break
                        else:
                            my_links = self.dc.net.links
                            for link in my_links:
                                if str(link.intf1) == old_stack.ports[port_name].intf_name and \
                                                str(link.intf1.ip) == old_stack.ports[port_name].ip_address.split('/')[
                                            0]:
                                    self._remove_link(server.name, link)
                                    break

                    # Create new links
                    for port_name in new_stack.servers[server.name].port_names:
                        if port_name not in server.port_names:
                            self._add_link(server.name,
                                           new_stack.ports[port_name].ip_address,
                                           new_stack.ports[port_name].intf_name,
                                           new_stack.ports[port_name].net_name)
            else:
                self._stop_compute(server)

        # Start all new servers
        for server in new_stack.servers.values():
            if server.name not in self.dc.containers:
                self._start_compute(server, new_stack)

        del self.stacks[old_stack_id]
        self.stacks[new_stack.id] = new_stack
        return True

    def _start_compute(self, server, stack=None):
        """ Starts a new compute object (docker container) inside the emulator
        Should only be called by stack modifications and not directly.
        :param server: emuvim.api.heat.resources.server
        :param stack: emuvim.api.heat.resources.stack
        :return:
        """
        logging.debug("Starting new compute resources %s" % server.name)
        network = list()

        for port_name in server.port_names:
            network_dict = dict()
            port = self.find_port_by_name_or_id(port_name)
            if port is not None:
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network_dict[network_dict['id']] = self.find_network_by_name_or_id(port.net_name).name
                network.append(network_dict)
        self.compute_nets[server.name] = network

        c = self.dc.startCompute(server.name, image=server.image, command=server.command, network=network)
        server.emulator_compute = c

        for intf in c.intfs.values():
            for port_name in server.port_names:
                port = self.find_port_by_name_or_id(port_name)
                if port is not None:
                    if intf.name == port.intf_name:
                        if port.mac_address is not None:
                            c.setMAC(port.mac_address)
                        else:
                            port.mac_address = intf.mac
                            # TODO: mac addresses in neutron_dummy_api!

        # Start the real emulator command now as specified in the dockerfile
        # ENV SON_EMU_CMD
        config = c.dcinfo.get("Config", dict())
        env = config.get("Env", list())
        for env_var in env:
            if "SON_EMU_CMD=" in env_var:
                cmd = str(env_var.split("=")[1])
                server.son_emu_command = cmd
                # execute command in new thread to ensure that GK is not blocked by VNF
                t = threading.Thread(target=c.cmdPrint, args=(cmd,))
                t.daemon = True
                t.start()

    def _stop_compute(self, server):
        logging.debug("Stopping container %s with full name %s" % (server.name, server.full_name))
        link_names = list()
        for port_name in server.port_names:
            link_names.append(self.find_port_by_name_or_id(port_name).intf_name)
            self.delete_port(port_name)
        my_links = self.dc.net.links
        for link in my_links:
            if str(link.intf1) in link_names:
                self._remove_link(server.name, link)

        self.dc.stopCompute(server.name)
        self.delete_server(server.name)

    def find_server_by_name_or_id(self, name_or_id):
        if name_or_id in self.computeUnits:
            return self.computeUnits[name_or_id]

        for server in self.computeUnits.values():
            if server.id == name_or_id or server.template_name == name_or_id or server.full_name == name_or_id:
                return server
        return None

    def create_server(self, name):
        if self.find_server_by_name_or_id(name) is not None:
            raise Exception("Server with name %s already exists." % name)
        server = Server(name)
        server.id = str(uuid.uuid4())
        self.computeUnits[server.id] = server
        return server

    def delete_server(self, name_or_id):
        server = self.find_server_by_name_or_id(name_or_id)
        if server is None:
            return False

        self.computeUnits.pop(name_or_id, None)

        # remove the server from any stack
        for stack in self.stacks.values():
            stack.servers.pop(server.name, None)

    def find_network_by_name_or_id(self, name_or_id):
        if name_or_id in self.nets:
            return self.nets[name_or_id]
        for net in self.nets.values():
            if net.name == name_or_id:
                return net

        return None

    def create_network(self, name):
        logging.debug("Creating network with name %s" % name)
        if self.find_network_by_name_or_id(name) is not None:
            logging.warning("Creating network with name %s failed, as it already exists" % name)
            raise Exception("Network with name %s already exists." % name)
        network = Net(name)
        network.id = str(uuid.uuid4())
        self.nets[network.id] = network
        return network

    def delete_network(self, name_or_id):
        net = self.find_network_by_name_or_id(name_or_id)
        if net is None:
            raise Exception("Network with name or id %s does not exists." % name_or_id)

        for stack in self.stacks.values():
            stack.nets.pop(net.name, None)

        self.nets.pop(net.id, None)

    def create_port(self, name):
        port = self.find_port_by_name_or_id(name)
        if port is not None:
            logging.warning("Creating port with name %s failed, as it already exists" % name)
            raise Exception("Port with name %s already exists." % name)
        logging.debug("Creating port with name %s" % name)
        port = Port(name)
        port.id = str(uuid.uuid4())
        self.ports[port.id] = port

        return port

    def find_port_by_name_or_id(self, name_or_id):
        if name_or_id in self.ports:
            return self.ports[name_or_id]
        for port in self.ports.values():
            if port.name == name_or_id or port.template_name == name_or_id:
                return port

        return None

    def delete_port(self, name_or_id):
        port = self.find_port_by_name_or_id(name_or_id)
        if port is None:
            raise Exception("Port with name or id %s does not exists." % name_or_id)

        my_links = self.dc.net.links
        for link in my_links:
            if str(link.intf1) == port.intf_name and \
                            str(link.intf1.ip) == port.ip_address.split('/')[0]:
                self._remove_link(link.intf1.node.name, link)
                break

        self.ports.pop(port.id, None)
        for stack in self.stacks.values():
            stack.ports.pop(port.name, None)

    def _add_link(self, node_name, ip_address, link_name, net_name):
        node = self.dc.net.get(node_name)
        params = {'params1': {'ip': ip_address,
                              'id': link_name,
                              link_name: net_name},
                  'intfName1': link_name,
                  'cls': Link}
        self.dc.net.addLink(node, self.dc.switch, **params)

    def _remove_link(self, server_name, link):
        self.dc.switch.detach(link.intf2)
        del self.dc.switch.intfs[self.dc.switch.ports[link.intf2]]
        del self.dc.switch.ports[link.intf2]
        del self.dc.switch.nameToIntf[link.intf2.name]
        self.dc.net.removeLink(link=link)
        self.dc.net.DCNetwork_graph.remove_edge(server_name, self.dc.switch.name)
        self.dc.net.DCNetwork_graph.remove_edge(self.dc.switch.name, server_name)
        for intf_key in self.dc.net[server_name].intfs.keys():
            if self.dc.net[server_name].intfs[intf_key].link == link:
                self.dc.net[server_name].intfs[intf_key].delete()
                del self.dc.net[server_name].intfs[intf_key]

    # Uses the container name to return the container ID
    def docker_container_id(self, container_name):
        c = Client()
        detail = c.inspect_container(container_name)
        if bool(detail["State"]["Running"]):
            return detail['Id']
        return None

    # Absolute number of nanoseconds the docker container used the CPU till startup and the current system time
    def docker_abs_cpu(self, container_id):
        with open('/sys/fs/cgroup/cpuacct/docker/' + container_id + '/cpuacct.usage_percpu', 'r') as f:
            line = f.readline()
        sys_time = int(time.time() * 1000000000)
        numbers = [int(x) for x in line.split()]
        cpu_usage = 0
        for number in numbers:
            cpu_usage += number
        return {'CPU_used': cpu_usage, 'CPU_used_systime': sys_time, 'CPU_cores': len(numbers)}

    # Bytes of memory used from the docker container
    def docker_mem_used(args, container_id):
        with open('/sys/fs/cgroup/memory/docker/' + container_id + '/memory.usage_in_bytes', 'r') as f:
            return int(f.readline())

    # Bytes of memory the docker container could use
    def docker_max_mem(self, container_id):
        with open('/sys/fs/cgroup/memory/docker/' + container_id + '/memory.limit_in_bytes', 'r') as f:
            mem_limit = int(f.readline())
        with open('/proc/meminfo', 'r') as f:
            line = f.readline().split()
        sys_value = int(line[1])
        unit = line[2]
        if unit == 'kB':
            sys_value *= 1024
        if unit == 'MB':
            sys_value *= 1024 * 1024

        if sys_value < mem_limit:
            return sys_value
        else:
            return mem_limit

    def docker_mem(self, container_id):
        out_dict = dict()
        out_dict['MEM_used'] = self.docker_mem_used(container_id)
        out_dict['MEM_limit'] = self.docker_max_mem(container_id)
        out_dict['MEM_%'] = float(out_dict['MEM_used']) / float(out_dict['MEM_limit'])
        return out_dict

    # Network traffic of all network interfaces within the controller
    def docker_abs_net_io(self, container_id):
        c = Client()
        command = c.exec_create(container_id, 'ifconfig')
        ifconfig = c.exec_start(command['Id'])
        sys_time = int(time.time() * 1000000000)

        in_bytes = 0
        m = re.findall('RX bytes:(\d+)', str(ifconfig))
        if m:
            for number in m:
                in_bytes += int(number)
        else:
            in_bytes = None

        out_bytes = 0
        m = re.findall('TX bytes:(\d+)', str(ifconfig))
        if m:
            for number in m:
                out_bytes += int(number)
        else:
            out_bytes = None

        return {'NET_in': in_bytes, 'NET_out': out_bytes, 'NET_systime': sys_time}

    # Disk - read in Bytes - write in Bytes
    def docker_block_rw(self, container_id):
        with open('/sys/fs/cgroup/blkio/docker/' + container_id + '/blkio.throttle.io_service_bytes', 'r') as f:
            read = f.readline().split()
            write = f.readline().split()
        rw_dict = dict()
        if len(read) < 3:
            rw_dict['BLOCK_read'] = 0
        else:
            rw_dict['BLOCK_read'] = read[2]
        if len(write) < 3:
            rw_dict['BLOCK_write'] = 0
        else:
            rw_dict['BLOCK_write'] = write[2]
        return rw_dict

    # Number of PIDS of that docker container
    def docker_PIDS(self, container_id):
        with open('/sys/fs/cgroup/cpuacct/docker/' + container_id + '/tasks', 'r') as f:
            return {'PIDS': len(f.read().split('\n'))-1}
