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

    @property
    def net(self):
        return self._net

    @net.setter
    def net(self, value):
        if self._net is None:
            self._net = value
            self.init_floating_network()
        self._net = value

    def init_floating_network(self):
        if self.net is not None and self.floating_switch is None:
            # create a floating network
            fn = self.floating_network = Net("floating-network")
            fn.id = str(uuid.uuid4())
            fn.set_cidr(self.floating_netmask)

            # create a subnet
            fn.subnet_id = str(uuid.uuid4())
            fn.subnet_name = fn.name + "-sub"

            # create a port for the host
            port = Port("root-port")
            port.id = str(uuid.uuid4())
            port.net_name = fn.name

            # get next free ip
            root_ip = fn.get_new_ip_address(port.name)
            port.ip_address = root_ip
            # floating ip network setup
            # wierd way of getting a datacenter object
            first_dc = self.net.dcs.values()[0]
            self.floating_switch = self.net.addSwitch("fs1", dpid=hex(first_dc._get_next_dc_dpid())[2:])
            # this is the interface appearing on the physical host
            self.floating_root = Node('root', inNamespace=False)
            self.floating_intf = self.net.addLink(self.floating_root, self.floating_switch).intf1
            self.floating_root.setIP(root_ip, intf=self.floating_intf)
            self.floating_root.cmd('route add -net ' + root_ip + ' dev ' + str(self.floating_intf))
            # for exclusive host-to-n connections
            # self.floating_switch.dpctl("add-flow", 'in_port=1,actions=NORMAL')
            # set up a simple learning switch
            self.floating_switch.dpctl("add-flow", 'actions=NORMAL')
            self.floating_nodes[(self.floating_root.name, root_ip)] = self.floating_root

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

    def _get_path(self, src_vnf, dst_vnf, src_vnf_intf, dst_vnf_intf):
        # modified version of the _chainAddFlow from emuvim.dcemulator.net._chainAddFlow
        src_sw = None
        dst_sw = None
        logging.debug("Find path from vnf %s to %s",
                      src_vnf, dst_vnf)

        for connected_sw in self.net.DCNetwork_graph.neighbors(src_vnf):
            link_dict = self.net.DCNetwork_graph[src_vnf][connected_sw]
            for link in link_dict:
                if (link_dict[link]['src_port_id'] == src_vnf_intf or
                            link_dict[link][
                                'src_port_name'] == src_vnf_intf):
                    # found the right link and connected switch
                    src_sw = connected_sw
                    break

        for connected_sw in self.net.DCNetwork_graph.neighbors(dst_vnf):
            link_dict = self.net.DCNetwork_graph[connected_sw][dst_vnf]
            for link in link_dict:
                if link_dict[link]['dst_port_id'] == dst_vnf_intf or \
                                link_dict[link][
                                    'dst_port_name'] == dst_vnf_intf:
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


    def add_loadbalancer(self, vnf_src_name, vnf_src_interface, lb_data):
        net = self.net
        src_sw_inport_nr = 0
        src_sw = None
        dest_intfs_mapping = lb_data.get('dst_vnf_interfaces', dict())

        # use all as default, as it is easiest for debugging purposes
        # ryu expects the type to be uppercase
        lb_type = lb_data.get('type', "ALL").upper()
        dest_vnf_outport_nrs = list()

        if vnf_src_name not in net:
            raise Exception(u"Source VNF does not exists.")

        # find the switch belonging to the source interface, as well as the inport nr
        for connected_sw in net.DCNetwork_graph.neighbors(vnf_src_name):
            link_dict = net.DCNetwork_graph[vnf_src_name][connected_sw]
            for link in link_dict:
                if link_dict[link]['src_port_name'] == vnf_src_interface:
                    src_sw = connected_sw
                    src_sw_inport_nr = link_dict[link]['dst_port_nr']
                    break

        if src_sw is None or src_sw_inport_nr == 0:
            raise Exception(u"Source VNF or interface can not be found.")

        # get all target interface outport numbers
        for vnf_name in dest_intfs_mapping:
            if vnf_name not in net.DCNetwork_graph:
                raise Exception(u"Target VNF %s is not known." % vnf_name)
            for connected_sw in net.DCNetwork_graph.neighbors(vnf_name):
                link_dict = net.DCNetwork_graph[vnf_name][connected_sw]
                for link in link_dict:
                    if link_dict[link]['src_port_name'] == dest_intfs_mapping[vnf_name]:
                        dest_vnf_outport_nrs.append(int(link_dict[link]['dst_port_nr']))

        # setup group table for load balancing on the first switch
        group_add = dict()
        # get first switch
        if (vnf_src_name, vnf_src_interface) not in self.lb_flow_cookies:
            self.lb_flow_cookies[(vnf_src_name, vnf_src_interface)] = list()

        src_intf = None
        src_ip = None
        src_mac_addr = None
        for intf in net[vnf_src_name].intfs.values():
            if intf.name == vnf_src_interface:
                src_mac_addr = intf.mac
                src_ip = intf.ip
                src_intf = intf

        if src_intf is None:
            raise Exception(u"Source VNF or interface can not be found.")

        group_add['dpid'] = int(net.getNodeByName(src_sw).dpid, 16)
        group_add['priority'] = 0
        group_add['type'] = lb_type
        group_id = self.get_flow_group(vnf_src_name, vnf_src_interface)
        group_add['group_id'] = group_id
        group_add['buckets'] = list()

        flows = list()
        # set up an initial flow that will set the LB group at the src interface
        flow = dict()
        flow['dpid'] = int(net.getNodeByName(src_sw).dpid, 16)
        flow['match'] = net._parse_match('in_port=%s' % src_sw_inport_nr)
        # cookie used by this flow
        cookie = self.get_cookie()
        self.lb_flow_cookies[(vnf_src_name, vnf_src_interface)].append(cookie)
        flow['cookie'] = cookie
        flow['priority'] = 1000
        action = dict()
        action['type'] = "GROUP"
        action['group_id'] = int(group_id)
        flow['actions'] = list()
        flow['actions'].append(action)
        logging.debug(flow)
        flows.append(flow)
        index = 0

        # set up paths for each destination vnf individually
        for dst_vnf_name, dst_vnf_interface in dest_intfs_mapping.iteritems():
            path, src_sw, dst_sw = self._get_path(vnf_src_name, dst_vnf_name,
                                                             vnf_src_interface, dst_vnf_interface)

            if dst_vnf_name not in net:
                self.delete_loadbalancer(vnf_src_name, vnf_src_interface)
                raise Exception(u"The destination VNF %s does not exist"% dst_vnf_name)
            if isinstance(path, dict):
                self.delete_loadbalancer(vnf_src_name, vnf_src_interface)
                raise Exception(u"Can not find a valid path. Are you specifying the right interfaces?.")

            mac_addr = "00:00:00:00:00:00"
            ip_addr = "0.0.0.0"
            for intf in net[dst_vnf_name].intfs.values():
                if intf.name == dst_vnf_interface:
                    mac_addr = str(intf.mac)
                    ip_addr = str(intf.ip)
            dst_sw_outport_nr = dest_vnf_outport_nrs[index]
            index += 1
            current_hop = src_sw
            switch_inport_nr = src_sw_inport_nr

            # choose free vlan if path contains more than 1 switch
            if len(path) > 1:
                vlan = net.vlans.pop()
            else:
                vlan = None

            for i in range(0, len(path)):
                current_node = net.getNodeByName(current_hop)
                if path.index(current_hop) < len(path) - 1:
                    next_hop = path[path.index(current_hop) + 1]
                else:
                    # last switch reached
                    next_hop = dst_vnf_name

                next_node = net.getNodeByName(next_hop)

                if next_hop == dst_vnf_name:
                    switch_outport_nr = dst_sw_outport_nr
                    logging.info("end node reached: {0}".format(dst_vnf_name))
                elif not isinstance(next_node, OVSSwitch):
                    logging.info("Next node: {0} is not a switch".format(next_hop))
                    return "Next node: {0} is not a switch".format(next_hop)
                else:
                    # take first link between switches by default
                    index_edge_out = 0
                    switch_outport_nr = net.DCNetwork_graph[current_hop][next_hop][index_edge_out]['src_port_nr']

                match = 'in_port=%s' % switch_inport_nr
                # possible Ryu actions, match fields:
                # http://ryu.readthedocs.io/en/latest/app/ofctl_rest.html#add-a-flow-entry
                # if a vlan is picked, the connection is routed through multiple switches
                if vlan is not None:
                    flow = dict()
                    flow['dpid'] = int(current_node.dpid, 16)
                    flow['cookie'] = cookie
                    flow['priority'] = 0

                    flow['actions'] = list()
                    if path.index(current_hop) == 0:  # first node
                        # set up a new bucket for forwarding
                        bucket = dict()
                        bucket['actions'] = list()

                        # set the vland field according to new ryu syntax
                        action = dict()
                        action['type'] = 'PUSH_VLAN'  # Push a new VLAN tag if a input frame is non-VLAN-tagged
                        action['ethertype'] = 33024  # Ethertype 0x8100(=33024): IEEE 802.1Q VLAN-tagged frame
                        bucket['actions'].append(action)
                        action = dict()
                        action['type'] = 'SET_FIELD'
                        action['field'] = 'vlan_vid'
                        # ryu expects the field to be masked
                        action['value'] = vlan | 0x1000
                        bucket['actions'].append(action)

                        # rewrite dst_mac
                        action = dict()
                        action['type'] = 'SET_FIELD'
                        action['field'] = 'eth_dst'
                        action['value'] = mac_addr
                        bucket['actions'].append(action)

                        # rewrite dst_ip
                        action = dict()
                        action['type'] = 'SET_FIELD'
                        action['field'] = 'ipv4_dst'
                        action['value'] = ip_addr
                        bucket['actions'].append(action)

                        # finally output the packet to the next switch
                        action = dict()
                        action['type'] = 'OUTPUT'
                        action['port'] = switch_outport_nr
                        bucket['actions'].append(action)

                        group_add["buckets"].append(bucket)
                        logging.debug(
                            "Appending bucket %s. src vnf %s to dst vnf %s" % (bucket, vnf_src_name, dst_vnf_name))
                    elif path.index(current_hop) == len(path) - 1:  # last node
                        match += ',dl_vlan=%s' % vlan
                        action = dict()
                        action['type'] = 'POP_VLAN'
                        flow['actions'].append(action)
                    else:  # middle nodes
                        match += ',dl_vlan=%s' % vlan

                    if not path.index(current_hop) == 0:
                        # this needs to be set for every hop that is not the first one
                        # as the first one is handled in the group entry
                        action = dict()
                        action['type'] = 'OUTPUT'
                        action['port'] = switch_outport_nr
                        flow['actions'].append(action)
                        flow['match'] = net._parse_match(match)
                        flows.append(flow)
                else:
                    # dest is connected to the same switch so just choose the right port to forward to
                    bucket = dict()
                    bucket['actions'] = list()

                    # rewrite dst_mac
                    action = dict()
                    action['type'] = 'SET_FIELD'
                    action['field'] = 'eth_dst'
                    action['value'] = mac_addr
                    bucket['actions'].append(action)

                    # rewrite dst_ip
                    action = dict()
                    action['type'] = 'SET_FIELD'
                    action['field'] = 'ipv4_dst'
                    action['value'] = ip_addr
                    bucket['actions'].append(action)

                    action = dict()
                    action['type'] = 'OUTPUT'
                    action['port'] = dst_sw_outport_nr
                    bucket['actions'].append(action)
                    group_add["buckets"].append(bucket)

                # set next hop for the next iteration step
                if isinstance(next_node, OVSSwitch):
                    switch_inport_nr = net.DCNetwork_graph[current_hop][next_hop][0]['dst_port_nr']
                    current_hop = next_hop

            # set up chain to enable answers
            flow_cookie = self.get_cookie()
            self.network_action_start(dst_vnf_name, vnf_src_name,
                                                 vnf_src_interface=dst_vnf_interface,
                                                 vnf_dst_interface=vnf_src_interface, bidirectional=False,
                                                 cookie=flow_cookie)
            self.lb_flow_cookies[(vnf_src_name, vnf_src_interface)].append(flow_cookie)

        # always create the group before adding the flow entries
        logging.debug("Setting up groupentry %s" % group_add)
        if net.controller == RemoteController:
            net.ryu_REST("stats/groupentry/add", data=group_add)

        for flow in flows:
            logging.debug("Setting up flowentry %s" % flow)
            if net.controller == RemoteController:
                net.ryu_REST('stats/flowentry/add', data=flow)

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

        logging.debug("Deleting group with id %s" % group_id)
        for switch_del_group in delete_group:
            if self.net.controller == RemoteController:
                self.net.ryu_REST("stats/groupentry/delete", data=switch_del_group)

        # unmap groupid from the interface
        del self.flow_groups[(vnf_src_name, vnf_src_interface)]
