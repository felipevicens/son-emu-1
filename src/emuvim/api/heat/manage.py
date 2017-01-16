"""Openstack manage component of PG Sandman.

.. module:: manage
    :synopsis: Module containing the OpenstackManage class.
.. moduleauthor: PG Sandman

"""

import logging
import threading
import uuid
import networkx as nx
import chain_api
from emuvim.api.heat.resources import Net, Port
from mininet.node import OVSSwitch, RemoteController, Node


class OpenstackManage(object):
    """
    OpenstackManage is a singleton and management component for the emulator.
    It is the brain of the Openstack component and manages everything that is not datacenter specific like
    network chains or load balancers.
    """
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
        """
        Initialize the floating network component for the emulator.
        Will not do anything if already initialized.
        """
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
            # set a dpid for the switch. for this we have to get the id of the next possible dc
            self.floating_switch = self.net.addSwitch("fs1", dpid=hex(first_dc._get_next_dc_dpid())[2:])
            # this is the interface appearing on the physical host
            self.floating_root = Node('root', inNamespace=False)
            self.net.hosts.append(self.floating_root)
            self.net.nameToNode['root'] = self.floating_root
            self.floating_intf = self.net.addLink(self.floating_root, self.floating_switch).intf1
            self.floating_root.setIP(root_ip, intf=self.floating_intf)
            #self.floating_root.cmd('route add -net "' + root_ip + '" dev ' + str(self.floating_intf))
            # for exclusive host-to-n connections
            # self.floating_switch.dpctl("add-flow", 'in_port=1,actions=NORMAL')
            # set up a simple learning switch
            self.floating_switch.dpctl("add-flow", 'actions=NORMAL')
            self.floating_nodes[(self.floating_root.name, root_ip)] = self.floating_root

    def add_endpoint(self, ep):
        """
        Registers an openstack endpoint with manage

        :param ep: Openstack API endpoint
        :type ep: :class:`heat.openstack_api_endpoint`
        """
        key = "%s:%s" % (ep.ip, ep.port)
        self.endpoints[key] = ep

    def get_cookie(self):
        """
        Get an unused cookie.

        :return: Cookie
        :rtype: ``int``
        """
        cookie = int(max(self.cookies) + 1)
        self.cookies.add(cookie)
        return cookie

    def get_flow_group(self, src_vnf_name, src_vnf_interface):
        """
        Gets free group that is not currently used by any other flow for the specified interface / VNF.

        :param src_vnf_name: Source VNF name
        :type src_vnf_name: ``str``
        :param src_vnf_interface: Source VNF interface name
        :type src_vnf_interface: ``str``
        :return: Flow group identifier.
        :rtype: ``int``
        """
        if (src_vnf_name, src_vnf_interface) not in self.flow_groups:
            grp = int(len(self.flow_groups) + 1)
            self.flow_groups[(src_vnf_name, src_vnf_interface)] = grp
        else:
            grp = self.flow_groups[(src_vnf_name, src_vnf_interface)]
        return grp

    def network_action_start(self, vnf_src_name, vnf_dst_name, **kwargs):
        """
        Starts a network chain for a source destination pair

        :param vnf_src_name: Name of the source VNF
        :type vnf_src_name: ``str``
        :param vnf_dst_name: Name of the source VNF interface
        :type vnf_dst_name: ``str``
        :param \**kwargs: See below

        :Keyword Arguments:
            * *vnf_src_interface* (``str``): Name of source interface.
            * *vnf_dst_interface* (``str``): Name of destination interface.
            * *weight* (``int``): This value is fed into the shortest path computation if no path is specified.
            * *match* (``str``): A custom match entry for the openflow flow rules. Only vlanid or port possible.
            * *bidirectional* (``bool``): If set the chain will be set in both directions, else it will just set up \
                            from source to destination.
            * *cookie* (``int``): Cookie value used by openflow. Used to identify the flows in the switches to be \
                            able to modify the correct flows.
            * *no_route* (``bool``): If set a layer 3 route to the target interface will not be set up.
        :return: The cookie chosen for the flow.
        :rtype: ``int``
        """
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
                cookie=kwargs.get('cookie', cookie),
                path=kwargs.get('path'))

            # add route to dst ip to this interface
            if not kwargs.get('no_route'):
                src_node = self.net.getNodeByName(vnf_src_name)
                dst_node = self.net.getNodeByName(vnf_dst_name)
                src_node.setHostRoute(dst_node.intf(kwargs.get('vnf_dst_interface')).IP(),
                                      kwargs.get('vnf_src_interface'))
                if kwargs.get('bidirectional'):
                    dst_node.setHostRoute(src_node.intf(kwargs.get('vnf_src_interface')).IP(),
                                          kwargs.get('vnf_dst_interface'))
            return cookie
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def network_action_stop(self, vnf_src_name, vnf_dst_name, **kwargs):
        """
        Starts a network chain for a source destination pair

        :param vnf_src_name: Name of the source VNF
        :type vnf_src_name: ``str``
        :param vnf_dst_name: Name of the source VNF interface
        :type vnf_dst_name: ``str``
        :param \**kwargs: See below

        :Keyword Arguments:
            * *vnf_src_interface* (``str``): Name of source interface.
            * *vnf_dst_interface* (``str``): Name of destination interface.
            * *bidirectional* (``bool``): If set the chain will be torn down in both directions, else it will just\
                            be torn down from source to destination.
            * *cookie* (``int``): Cookie value used by openflow. Used to identify the flows in the switches to be \
                            able to modify the correct flows.
        """
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
        """
        Own implementation of the get_path function from DCNetwork, because we just want the path and not set up
        flows on the way.

        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param src_vnf_intf: Name of the source VNF interface
        :type src_vnf_intf: ``str``
        :param dst_vnf_intf: Name of the destination VNF interface
        :type dst_vnf_intf: ``str``
        :return: path, src_sw, dst_sw
        :rtype: ``list``, ``str``, ``str``
        """
        # modified version of the _chainAddFlow from emuvim.dcemulator.net._chainAddFlow
        src_sw = None
        dst_sw = None
        logging.debug("Find shortest path from vnf %s to %s",
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

        logging.info("Shortest path between {0} and {1}: {2}".format(src_vnf, dst_vnf, path))
        return path, src_sw, dst_sw

    def add_loadbalancer(self, src_vnf_name, src_vnf_interface, lb_data):
        """
        This function will set up a loadbalancer at the given interface.

        :param src_vnf_name: Name of the source VNF
        :type src_vnf_name: ``str``
        :param src_vnf_interface: Name of the destination VNF
        :type src_vnf_interface: ``str``
        :param lb_data: A dictionary containing the destination data as well as custom path settings
        :type lb_data: ``dict``

        :Example:
        lbdata = {"dst_vnf_interfaces": {"dc2_man_web0": "port-man-2",
        "dc3_man_web0": "port-man-4","dc4_man_web0": "port-man-6"}, "path": {"dc2_man_web0": {"port-man-2": [ "dc1.s1",\
        "s1", "dc2.s1"]}}}
        """
        net = self.net
        src_sw_inport_nr = 0
        src_sw = None
        dest_intfs_mapping = lb_data.get('dst_vnf_interfaces', dict())
        # a custom path can be specified as a list of switches
        custom_paths = lb_data.get('path', dict())
        dest_vnf_outport_nrs = list()

        logging.debug("Call to add_loadbalancer at %s intfs:%s" % (src_vnf_name, src_vnf_interface))

        if src_vnf_name not in net:
            raise Exception(u"Source VNF does not exists.")

        # find the switch belonging to the source interface, as well as the inport nr
        for connected_sw in net.DCNetwork_graph.neighbors(src_vnf_name):
            link_dict = net.DCNetwork_graph[src_vnf_name][connected_sw]
            for link in link_dict:
                if link_dict[link]['src_port_name'] == src_vnf_interface:
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
        # get first switch
        if (src_vnf_name, src_vnf_interface) not in self.lb_flow_cookies:
            self.lb_flow_cookies[(src_vnf_name, src_vnf_interface)] = list()

        src_intf = None
        src_ip = None
        src_mac = None
        for intf in net[src_vnf_name].intfs.values():
            if intf.name == src_vnf_interface:
                src_mac = intf.mac
                src_ip = intf.ip
                src_intf = intf

        if src_intf is None:
            raise Exception(u"Source VNF or interface can not be found.")

        # set up paths for each destination vnf individually
        index = 0
        cookie = self.get_cookie()
        main_cmd = "add-flow -OOpenFlow13"
        self.lb_flow_cookies[(src_vnf_name, src_vnf_interface)].append(cookie)
        for dst_vnf_name, dst_vnf_interface in dest_intfs_mapping.iteritems():
            path, src_sw, dst_sw = self._get_path(src_vnf_name, dst_vnf_name,
                                                  src_vnf_interface, dst_vnf_interface)

            # use custom path if one is supplied
            # json does not support hashing on tuples so we use nested dicts
            if dst_vnf_name in custom_paths:
                if dst_vnf_interface in custom_paths[dst_vnf_name]:
                    path = custom_paths[dst_vnf_name][dst_vnf_interface]
                    logging.debug("Taking custom path from %s to %s: %s" % (src_vnf_name, dst_vnf_name, path))

            if dst_vnf_name not in net:
                self.delete_loadbalancer(src_vnf_name, src_vnf_interface)
                raise Exception(u"The destination VNF %s does not exist" % dst_vnf_name)
            if isinstance(path, dict):
                self.delete_loadbalancer(src_vnf_name, src_vnf_interface)
                raise Exception(u"Can not find a valid path. Are you specifying the right interfaces?.")

            target_mac = "fa:17:00:03:13:37"
            target_ip = "0.0.0.0"
            for intf in net[dst_vnf_name].intfs.values():
                if intf.name == dst_vnf_interface:
                    target_mac = str(intf.mac)
                    target_ip = str(intf.ip)
            dst_sw_outport_nr = dest_vnf_outport_nrs[index]
            current_hop = src_sw
            switch_inport_nr = src_sw_inport_nr
            self.setup_arp_reply_at(src_sw, src_sw_inport_nr, target_ip, target_mac, cookie=cookie)
            # choose free vlan if path contains more than 1 switch
            if len(path) > 1:
                vlan = net.vlans.pop()
            else:
                vlan = None

            for i in range(0, len(path)):
                if i < len(path) - 1:
                    next_hop = path[i+1]
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

                cmd = '",priority=1,in_port=%s' % switch_inport_nr
                # if a vlan is picked, the connection is routed through multiple switches
                if vlan is not None:
                    if path.index(current_hop) == 0:  # first node
                        # flow #index set up
                        cmd = '"in_port=%s' % src_sw_inport_nr
                        cmd += ',cookie=%s' % cookie
                        cmd += ',table=%s' % cookie
                        cmd += ',ip'
                        cmd += ',reg1=%s' % index
                        cmd += ',actions='
                        # set vlan id
                        cmd += ',push_vlan:0x8100'
                        masked_vlan = vlan | 0x1000
                        cmd += ',set_field:%s->vlan_vid' % masked_vlan
                        cmd += ',set_field:%s->eth_dst' % target_mac
                        cmd += ',set_field:%s->ip_dst' % target_ip
                        cmd += ',output:%s"' % switch_outport_nr
                    elif next_hop == dst_vnf_name:  # last switch
                        # remove any vlan tags
                        cmd += ',dl_vlan=%s' % vlan
                        cmd += ',actions=pop_vlan,output:%s"' % switch_outport_nr
                        # set up arp replys at the port so the dst nodes know the src
                        self.setup_arp_reply_at(current_hop, switch_outport_nr, src_ip, src_mac, cookie=cookie)
                    else:  # middle nodes
                        # if we have a circle in the path we need to specify this, as openflow will ignore the packet
                        # if we just output it on the same port as it came in
                        if switch_inport_nr == switch_outport_nr:
                            cmd += ',dl_vlan=%s,actions=IN_PORT"' % (vlan)
                        else:
                            cmd += ',dl_vlan=%s,actions=output:%s"' % (vlan, switch_outport_nr)
                # output the packet at the correct outport
                else:
                    cmd += ',actions=output:%s"' % switch_outport_nr

                # excecute the command on the target switch
                logging.debug(cmd)
                net[current_hop].dpctl(main_cmd, cmd)
                # set next hop for the next iteration step
                if isinstance(next_node, OVSSwitch):
                    switch_inport_nr = net.DCNetwork_graph[current_hop][next_hop][0]['dst_port_nr']
                    current_hop = next_hop

            # set up chain to enable answers
            self.network_action_start(dst_vnf_name, src_vnf_name,
                                      vnf_src_interface=dst_vnf_interface,
                                      vnf_dst_interface=src_vnf_interface, bidirectional=False,
                                      cookie=cookie, path=list(reversed(path)))
            index += 1

        # set up the actual load balancing rule as a multipath on the very first switch
        cmd = '"in_port=%s' % src_sw_inport_nr
        cmd += ',cookie=%s' % (cookie)
        cmd += ',ip'
        cmd += ',actions='
        # push 0x01 into the first register
        cmd += 'load:0x1->NXM_NX_REG0[]'
        # load balance modulo n over all dest interfaces
        # TODO: in newer openvswitch implementations this should be changed to symmetric_l3l4+udp
        # to balance any kind of traffic
        cmd += ',multipath(symmetric_l4,1024,modulo_n,%s,0,NXM_NX_REG1[0..12])' % len(dest_intfs_mapping)
        # reuse the cookie as table entry as it will be unique
        cmd += ',resubmit(, %s)"' % cookie

        # actually add the flow
        logging.debug("Switch: %s, CMD: %s" % (src_sw, cmd))
        net[src_sw].dpctl(main_cmd, cmd)

    def setup_arp_reply_at(self, switch, port_nr, target_ip, target_mac, cookie=None):
        """
        Sets up a custom ARP reply at a switch.
        An ARP request coming in on the `port_nr` for `target_ip` will be answered with target IP/MAC.

        :param switch: The switch belonging to the interface
        :type switch: ``str``
        :param port_nr: The port number at the switch that is connected to the interface
        :type port_nr: ``int``
        :param target_ip: The IP for which to set up the ARP reply
        :type target_ip: ``str``
        :param target_mac: The MAC address of the target interface
        :type target_mac: ``str``
        :param cookie: cookie to identify the ARP request, if None a new one will be picked
        :type cookie: ``int`` or ``None``
        :return: cookie
        :rtype: ``int``
        """
        if cookie is None:
            cookie = self.get_cookie()
        main_cmd = "add-flow -OOpenFlow13"

        # first set up ARP requests for the source node, so it will always 'find' a partner
        cmd = '"in_port=%s' % port_nr
        cmd += ',cookie=%s' % cookie
        cmd += ',arp'
        # set target arp ip
        cmd += ',arp_tpa=%s' % target_ip
        cmd += ',actions='
        # set message type to ARP reply
        cmd += 'load:0x2->NXM_OF_ARP_OP[]'
        # set src ip as dst ip
        cmd += ',move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[]'
        # set src mac
        cmd += ',set_field:%s->eth_src' % target_mac
        # set src as target
        cmd += ',move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[], move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[]'
        # set target mac as hex
        cmd += ',load:0x%s->NXM_NX_ARP_SHA[]' % "".join(target_mac.split(':'))
        # set target ip as hex
        octets = target_ip.split('.')
        dst_ip_hex = '{:02X}{:02X}{:02X}{:02X}'.format(*map(int, octets))
        cmd += ',load:0x%s->NXM_OF_ARP_SPA[]' % dst_ip_hex
        # output to incoming port remember the closing "
        cmd += ',IN_PORT"'
        self.net[switch].dpctl(main_cmd, cmd)
        logging.debug(
            "Set up ARP reply at %s port %s." % (switch, port_nr))

    def delete_loadbalancer(self, vnf_src_name, vnf_src_interface):
        '''
        Removes a loadbalancer that is configured for the node and interface

        :param src_vnf_name: Name of the source VNF
        :param src_vnf_interface: Name of the destination VNF
        :return: None
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
