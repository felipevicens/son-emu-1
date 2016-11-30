import logging
import re
import chain_api
import threading
import networkx as nx
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.heat.resources import Net, Port
from emuvim.api.heat.openstack_dummies.neutron_dummy_api import NeutronDummyApi
import uuid
from mininet.node import OVSSwitch, RemoteController, Controller, Node
from mininet.util import ipAdd
from mininet.net import Mininet as mn

# force full debug logging everywhere for now
logging.getLogger().setLevel(logging.DEBUG)


class OpenstackManage(object):
    # openstackmanage is a singleton!
    __instance = None

    def __new__(cls):
        if OpenstackManage.__instance is None:
            OpenstackManage.__instance = object.__new__(cls)
        return OpenstackManage.__instance

    def __init__(self, ip="0.0.0.0", port=4000):
        self.endpoints = dict()
        self.cookies = set()
        self.cookies.add(0)
        self.ip = ip
        self.port = port
        self._net = None
        # to keep track which src_vnf(input port on the switch) handles a load balancer
        self.lb_flow_cookies = dict()
        # flow groups could be handled for each switch separately, but this global group counter should be easier to
        # debug and to maintain
        self.flow_groups = dict()

        # we want one global chain api. this should not be datacenter dependent!
        if not hasattr(self, "chain"):
            self.chain = chain_api.ChainApi(ip, port, self)
        if not hasattr(self, "thread"):
            self.thread = threading.Thread(target=self.chain._start_flask, args=())
            self.thread.daemon = True
            self.thread.name = self.chain.__class__
            self.thread.start()

        # floating ip network setup
        self.floating_switch = None
        self.floating_network = None
        self.floating_netmask = "192.168.100.0/24"
        self.floating_nodes = dict()
        self.floating_intf = None
        self._floating_last_ip = 3

    @property
    def net(self):
        return self._net

    @net.setter
    def net(self, value):
        if self._net is None:
            self._net = value
            self.init_floating_network()
        self._net = value

    @property
    def floating_next_ip(self):
        ip, netmask = self.floating_netmask.split("/")[0]
        next_ip = ipAdd(self._floating_last_ip, ip, netmask) +"/"+ netmask
        self._floating_last_ip += 1
        return next_ip

    def init_floating_network(self):
        if self.net is not None and self.floating_switch is None:
            fn = self.floating_network = Net("floating-network")
            fn.id = str(uuid.uuid4())
            fn.set_cidr(self.floating_netmask)
            fn.subnet_id = str(uuid.uuid4())
            fn.subnet_name = fn.name + "-sub"
            port = Port("root-port")
            port.id = str(uuid.uuid4())
            port.net_name = fn.name
            root_ip = fn.get_new_ip_address(port.name)
            port.ip_address = root_ip
            # floating ip network setup
            self.floating_switch = self.net.addSwitch("fs1")
            # this is the interface appearing on the physical host
            self.floating_root = Node('root', inNamespace=False)
            self.floating_intf = self.net.addLink(self.floating_root, self.floating_switch).intf1
            self.floating_root.setIP(root_ip, intf=self.floating_intf)
            self.floating_root.cmd('route add -net ' + root_ip + ' dev ' + str(self.floating_intf))
            self.floating_switch.dpctl("add-flow", 'action=NORMAL')
            self.floating_nodes[self.floating_root.name] = self.floating_root

    def add_endpoint(self, ep):
        key = "%s:%s" % (ep.ip, ep.port)
        self.endpoints[key] = ep

    def get_cookie(self):
        cookie = int(max(self.cookies) + 1)
        self.cookies.add(cookie)
        return cookie

    def get_flow_group(self, src_vnf_name, src_vnf_interface):
        if (src_vnf_name, src_vnf_interface) not in self.flow_groups:
            grp = int(len(self.flow_groups) + 1)
            self.flow_groups[(src_vnf_name, src_vnf_interface)] = grp
        else:
            grp = self.flow_groups[(src_vnf_name, src_vnf_interface)]
        return grp

    def network_action_start(self, vnf_src_name, vnf_dst_name, **kwargs):
        try:
            cookie = kwargs.get('cookie', self.get_cookie())
            self.cookies.add(cookie)
            c = self.net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=kwargs.get('vnf_src_interface'),
                vnf_dst_interface=kwargs.get('vnf_dst_interface'),
                cmd='add-flow',
                weight=kwargs.get('weight'),
                match=kwargs.get('match'),
                bidirectional=kwargs.get('bidirectional'),
                cookie=kwargs.get('cookie', cookie))
            return cookie
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def network_action_stop(self, vnf_src_name, vnf_dst_name, **kwargs):
        # call DCNetwork method, not really datacenter specific API for now...
        # provided dc name needs to be part of API endpoint
        # no check if vnfs are really connected to this datacenter...
        try:
            c = self.net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=kwargs.get('vnf_src_interface'),
                vnf_dst_interface=kwargs.get('vnf_dst_interface'),
                cmd='del-flows',
                weight=kwargs.get('weight'),
                match=kwargs.get('match'),
                bidirectional=kwargs.get('bidirectional'),
                cookie=kwargs.get('cookie'))
            if kwargs.get('cookie', 0) in self.cookies:
                self.cookies.remove(kwargs.get('cookie', 0))
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def _get_path(self, src_vnf, dst_vnf):
        # modified version of the _chainAddFlow from emuvim.dcemulator.net._chainAddFlow
        src_sw = None
        dst_sw = None
        logging.debug("Find path from vnf %s to %s",
                      src_vnf, dst_vnf)

        for connected_sw in self.net.DCNetwork_graph.neighbors(src_vnf):
            link_dict = self.net.DCNetwork_graph[src_vnf][connected_sw]
            for link in link_dict:
                for intfs in self.net[src_vnf].intfs.values():
                    if (link_dict[link]['src_port_id'] == intfs.name or
                                link_dict[link][
                                    'src_port_name'] == intfs.name):  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                        # found the right link and connected switch
                        src_sw = connected_sw
                        break

        for connected_sw in self.net.DCNetwork_graph.neighbors(dst_vnf):
            link_dict = self.net.DCNetwork_graph[connected_sw][dst_vnf]
            for link in link_dict:
                for intfs in self.net[dst_vnf].intfs.values():
                    if link_dict[link]['dst_port_id'] == intfs.name or \
                                    link_dict[link][
                                        'dst_port_name'] == intfs.name:  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                        # found the right link and connected
                        dst_sw = connected_sw
                        break
        logging.debug("From switch %s to %s " % (src_sw, dst_sw))

        # get shortest path
        try:
            # returns the first found shortest path
            # if all shortest paths are wanted, use: all_shortest_paths
            path = nx.shortest_path(self.net.DCNetwork_graph, src_sw, dst_sw)
        except:
            logging.exception("No path could be found between {0} and {1} using src_sw={2} and dst_sw={3}".format(
                src_vnf, dst_vnf, src_sw, dst_sw))
            logging.debug("Graph nodes: %r" % self.net.DCNetwork_graph.nodes())
            logging.debug("Graph edges: %r" % self.net.DCNetwork_graph.edges())
            for e, v in self.net.DCNetwork_graph.edges():
                logging.debug("%r" % self.net.DCNetwork_graph[e][v])
            return "No path could be found between {0} and {1}".format(src_vnf, dst_vnf)

        logging.info("Path between {0} and {1}: {2}".format(src_vnf, dst_vnf, path))
        return path, src_sw, dst_sw

    def convert_ryu_to_ofctl(self, flow, ofctl_cmd="add-flow"):
        def convert_action_to_string(act):
            cmd = ""
            # remember to escape strings as the commandline is used!
            if act.get("type") == "POP_VLAN":
                cmd += "strip_vlan,"
            if act.get("type") == "PUSH_VLAN":
                cmd += "push_vlan:%s," % hex(act.get("ethertype"))
            if "field" in act and "vlan_vid" in act["field"] and act.get("type") == "SET_FIELD":
                cmd += "set_field=%s-\>vlan_vid," % act.get("value")
            if act.get("type") == "OUTPUT":
                cmd += "output:%s," % int(act.get('port'))
            if act.get("type") == "GROUP":
                cmd += "group:%d" % act.get("group_id")
            return cmd.rstrip(",")

        cmd = "-O OpenFlow13 "
        target_switch = None
        # get the corresponding name of the datapath id
        for node in self.net.switches:
            if isinstance(node, OVSSwitch) and int(node.dpid, 16) == flow['dpid']:
                target_switch = node
                break
        if target_switch is None:
            raise Exception("Convert_ryu_to_ofctl: Failed to find datapath id %s" % flow['dpid'])
        if ofctl_cmd == "add-flow" or ofctl_cmd == "add-group":
            if "group_id" in flow:
                cmd += "group_id=%s," % flow.get("group_id")
                cmd += "type=%s," % flow.get("type").lower()
                if "buckets" in flow:
                    for bucket in flow["buckets"]:
                        cmd += "bucket="
                        # TODO: get correct weight field!
                        if flow.get("type") == "select":
                            cmd += "weight:%s," % bucket.get("weight", 0)
                        # buckets do not contain an action keyword!
                        for action in bucket.get("actions"):
                            cmd += "%s," % convert_action_to_string(action)
                    cmd = cmd.rstrip(",")

            else:
                if "priority" in flow:
                    cmd += "priority=%s," % flow.get("priority")
                if "cookie" in flow:
                    cmd += "cookie=%s," % flow.get("cookie")
                if "match" in flow:
                    for key, match in flow.get("match").iteritems():
                        cmd += "%s=%s," % (key, match)
                    cmd = cmd.rstrip(",")

                cmd += ",actions="
                for action in flow.get("actions"):
                    cmd += "%s," % convert_action_to_string(action)

        if ofctl_cmd == "del-flows":
            cmd += "cookie=%s/%s" % (flow.get("cookie"), flow.get("cookie_mask"))
        if ofctl_cmd == "del-groups":
            cmd += "group_id=%s" % flow.get("group_id")

        cmd = cmd.rstrip(",")
        logging.debug("Converted string is: %s %s" % (ofctl_cmd, cmd))

        target_switch.dpctl(ofctl_cmd, cmd)

    def delete_loadbalancer(self, vnf_src_name, vnf_src_interface):
        '''
        Removes a loadbalancer that is configured for the node and interface
        :param vnf_src_name:
        :param vnf_src_interface:
        :return:
        '''
        flows = list()
        # we have to call delete-group for each switch
        delete_group = list()
        group_id = self.get_flow_group(vnf_src_name, vnf_src_interface)
        for node in self.net.switches:
            for cookie in self.lb_flow_cookies[(vnf_src_name, vnf_src_interface)]:
                flow = dict()
                flow["dpid"] = int(node.dpid, 16)
                flow["cookie"] = cookie
                flow['cookie_mask'] = int('0xffffffffffffffff', 16)

                flows.append(flow)
            group_del = dict()
            group_del["dpid"] = int(node.dpid, 16)
            group_del["group_id"] = group_id
            delete_group.append(group_del)

        for flow in flows:
            logging.debug("Deleting flowentry with cookie %d belonging to lb at %s:%s" % (
                flow["cookie"], vnf_src_name, vnf_src_interface))
            if self.net.controller == RemoteController:
                self.net.ryu_REST('stats/flowentry/delete', data=flow)
            else:
                self.convert_ryu_to_ofctl(flow, "del-flows")

        logging.debug("Deleting group with id %s" % group_id)
        for switch_del_group in delete_group:
            if self.net.controller == RemoteController:
                self.net.ryu_REST("stats/groupentry/delete", data=switch_del_group)
            else:
                self.convert_ryu_to_ofctl(switch_del_group, "del-groups")

        # unmap groupid from the interface
        del self.flow_groups[(vnf_src_name, vnf_src_interface)]