from mininet.link import Link
from resources import *
from docker import Client
from docker.utils import kwargs_from_env
import logging
import threading
import re
import os
import subprocess


logging.basicConfig(level=logging.DEBUG)


class HeatApiStackInvalidException(BaseException):
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

    def add_stack(self, stack):
        if not self.check_stack(stack):
            raise HeatApiStackInvalidException("Stack did not pass validity checks")
        self.stacks[stack.id] = stack

    def check_stack(self, stack):
        for server in stack.servers.values():
            for port_name in server.port_names:
                if port_name not in stack.ports:
                    return False
        for port in stack.ports.values():
            if port.net_name not in stack.nets:
                return False
        for router in stack.routers.values():
            for subnet_name in router.subnet_names:
                found = False
                for net in stack.nets.values():
                    if net.subnet_name == subnet_name:
                        found = True
                        break
                if not found:
                    return False
        return True

    def add_flavor(self, name, cpu, memory, memory_unit, storage, storage_unit):
        flavor = InstanceFlavor(name, cpu, memory, memory_unit, storage, storage_unit)
        self.flavors[flavor.id] = flavor

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
            self._stop_compute(server, self.stacks[stack_id])

        del self.stacks[stack_id]

    def update_stack(self, old_stack_id, new_stack):
        if old_stack_id in self.stacks:
            if not self.check_stack(new_stack):
                return False
            old_stack = self.stacks[old_stack_id]
        else:
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
                    self._stop_compute(server, old_stack)
                else:
                    # Delete unused and changed links
                    for port_name in server.port_names:
                        if port_name in old_stack.ports and port_name in new_stack.ports:
                            if not old_stack.ports.get(port_name) == new_stack.ports.get(port_name):
                                my_links = self.dc.net.links
                                for link in my_links:
                                    if str(link.intf1) == old_stack.ports[port_name].intf_name and \
                                       str(link.intf1.ip) == old_stack.ports[port_name].ip_address.split('/')[0]:
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
                                   str(link.intf1.ip) == old_stack.ports[port_name].ip_address.split('/')[0]:
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
                self._stop_compute(server, old_stack)

        # Start all new servers
        for server in new_stack.servers.values():
            if server.name not in self.dc.containers:
                self._start_compute(server, new_stack)

        del self.stacks[old_stack_id]
        self.stacks[new_stack.id] = new_stack
        return True

    def _start_compute(self, server, stack):
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
            network_dict['id'] = stack.ports[port_name].intf_name
            network_dict['ip'] = stack.ports[port_name].ip_address
            network_dict[network_dict['id']] = stack.nets[stack.ports[port_name].net_name].name
            network.append(network_dict)

        c = self.dc.startCompute(server.name, image=server.image, command=server.command, network=network)

        # Start the real emulator command now as specified in the dockerfile
        # ENV SON_EMU_CMD
        config = c.dcinfo.get("Config", dict())
        env = config.get("Env", list())
        for env_var in env:
            if "SON_EMU_CMD=" in env_var:
                cmd = str(env_var.split("=")[1])
                # execute command in new thread to ensure that GK is not blocked by VNF
                t = threading.Thread(target=c.cmdPrint, args=(cmd,))
                t.daemon = True
                t.start()

    def _stop_compute(self, server, stack):
        link_names = list()
        for port_name in server.port_names:
            link_names.append(str(stack.nets[stack.ports[port_name].net_name].get_short_id() +
                                  '-' + stack.ports[port_name].get_short_id()))
        my_links = self.dc.net.links
        for link in my_links:
            if str(link.intf1) in link_names:
                self._remove_link(server.name, link)
        self.dc.stopCompute(server.name)

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

    # Creates the monitoring data with 'docker stats'
    def monitor_container(self, container_name):
        c = Client(**(kwargs_from_env()))
        detail = c.inspect_container(container_name)

        if bool(detail["State"]["Running"]):
            container_id = detail['Id']

            docker_stat = subprocess.Popen(["docker", "stats", "--no-stream"], stdout=subprocess.PIPE)
            output = docker_stat.communicate()[0]

            for line in output.split('\n'):
                if line.split(' ')[0] == container_id[:12]:
                    return self.create_monitoring_dict(line)
        else:
            return None
        return None

    # Creates a dict for one container, out of the 'docker stats' output.
    def create_monitoring_dict(self, docker_stats_line):
        if docker_stats_line is None:
            return None
        split_line = docker_stats_line.split()
        if len(split_line) < 19:
            return None

        out_dict = dict()
        out_dict['CPU'] = split_line[1]
        out_dict['MEM_usage'] = split_line[2] + ' ' + split_line[3]
        out_dict['MEM_limit'] = split_line[5] + ' ' + split_line[6]
        out_dict['MEM_%'] = split_line[7]
        out_dict['NET_in'] = split_line[8] + ' ' + split_line[9]
        out_dict['NET_out'] = split_line[11] + ' ' + split_line[12]
        out_dict['PIDS'] = split_line[18]
        return out_dict

    # One way to go - not so nice, because we currently only get the seconds, the process was running
    def display_cpu(self, container_name):
        c = Client(**(kwargs_from_env()))
        detail = c.inspect_container(container_name)

        if bool(detail["State"]["Running"]):
            container_id = detail['Id']
            cpu_usage = {}
            with open('/sys/fs/cgroup/cpuacct/docker/' + container_id + '/cpuacct.stat', 'r') as f:
                for line in f:
                    m = re.search(r"(system|user)\s+(\d+)", line)
                    if m:
                        cpu_usage[m.group(1)] = int(m.group(2))  # CPU usage in seconds (or 100 Sec) since the start

            cpu = cpu_usage["system"] + cpu_usage["user"]
            user_ticks = os.sysconf(os.sysconf_names['SC_CLK_TCK'])
            print(float(cpu) / user_ticks)
        else:
            print(0)

    # Bytes of memory used from the docker container
    def display_memory(args, container_name):
        c = Client(**(kwargs_from_env()))
        detail = c.inspect_container(container_name)
        if bool(detail["State"]["Running"]):
            container_id = detail['Id']
            with open('/sys/fs/cgroup/memory/docker/' + container_id + '/memory.stat', 'r') as f:
                for line in f:
                    m = re.search(r"total_rss\s+(\d+)", line)
                    if m:
                        print(m.group(1))  # in Bytes! For MiB div by 1024*1024!
                        return
        print(0)
