from flask import Flask
from flask_restful import Api, Resource
from flask import Response, request
import logging
import json
from mininet.node import OVSSwitch, RemoteController


class ChainApi(Resource):
    def __init__(self, inc_ip, inc_port, manage):
        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.ip = inc_ip
        self.port = inc_port
        self.manage = manage
        self.api.add_resource(ChainVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnf, "/v1/chain/<src_vnf>/<dst_vnf>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnfInterfaces, "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnfDcStackInterfaces,
                              "/v1/chain/<src_dc>/<src_stack>/<src_vnf>/<src_intfs>/<dst_dc>/<dst_stack>/<dst_vnf>/<dst_intfs>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(BalanceHost, "/v1/lb/<vnf_src_name>/<vnf_src_interface>",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("ChainDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class ChainVersionsList(Resource):
    '''
    Entrypoint to find versions of the chain api.
    '''

    def __init__(self, api):
        self.api = api

    def get(self, id):
        # at least let it look like an open stack function
        try:
            resp = """[
                {
                    "versions": [
                        {
                            "id": "v1",
                            "links": [
                                {
                                    "href": "http://%s:%d/v1/",
                                    "rel": "self"
                                }
                            ],
                            "status": "CURRENT",
                            "version": "1",
                            "min_version": "1",
                            "updated": "2013-07-23T11:33:21Z"
                        }
                    ]
                }
            """ % (self.api.ip, self.api.port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class ChainVnf(Resource):
    '''
    Handles setting up a chain between two VNFs at "/v1/chain/<src_vnf>/<dst_vnf>"
    This Resource tries to guess on which interfaces to chain on
    '''

    def __init__(self, api):
        self.api = api

    def put(self, src_vnf, dst_vnf):
        '''
        A PUT request to "/v1/chain/<src_vnf>/<dst_vnf>/" will create a chain between the two VNFs.
        The interfaces will be guessed.
        :param src_vnf:
        :param dst_vnf:
        :return:
        '''
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")

        try:
            # check if which interface to chain on
            dst_intfs = None
            src_intfs = None

            for intfs in self.api.manage.net[src_vnf].intfs.values():
                for dintfs in self.api.manage.net[dst_vnf].intfs.values():
                    # if both are in the same network they can be chained
                    # TODO: may chain on the mgmt interface!!
                    if intfs.params[intfs.name] == dintfs.params[dintfs.name]:
                        src_intfs = intfs.name
                        dst_intfs = dintfs.name

            cookie = self.api.manage.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                          vnf_dst_interface=dst_intfs, bidirectional=True)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

    def delete(self, src_vnf, dst_vnf):
        '''
        A DELETE request at "/v1/chain/<src_vnf>/<dst_vnf>/"
        Will delete a previously set up chain between two interfaces
        :param src_vnf:
        :param dst_vnf:
        :return:
        '''
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")

        try:
            # check if which interface to chain on
            dst_intfs = None
            src_intfs = None

            for intfs in self.api.manage.net[src_vnf].intfs.values():
                for dintfs in self.api.manage.net[dst_vnf].intfs.values():
                    # if both are in the same network they can be chained
                    if intfs.params[intfs.name] == dintfs.params[dintfs.name]:
                        src_intfs = intfs.name
                        dst_intfs = dintfs.name

            cookie = self.api.manage.network_action_stop(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                         vnf_dst_interface=dst_intfs, bidirectional=True)

            return Response(json.dumps(cookie), status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain", status=500, mimetype="application/json")


class ChainVnfInterfaces(Resource):
    '''
    Handles requests targeted at: "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>"
    Handles tearing down or setting up a chain between two vnfs
    '''

    def __init__(self, api):
        self.api = api

    def put(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        '''
         A put request to "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>"
         will create a chain between two interfaces at the specified vnfs
        :param src_vnf:
        :param src_intfs:
        :param dst_vnf:
        :param dst_intfs:
        :return:
        '''
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            cookie = self.api.manage.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                          vnf_dst_interface=dst_intfs, bidirectional=True)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

    def delete(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        '''
        A DELETE request to "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>"
        will delete a previously created chain.
        :param src_vnf:
        :param src_intfs:
        :param dst_vnf:
        :param dst_intfs:
        :return:
        '''
        # check if both VNFs exist
        if src_vnf not in self.api.manage.net or dst_vnf not in self.api.manage.net:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")
        try:
            cookie = self.api.manage.network_action_stop(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                         vnf_dst_interface=dst_intfs, bidirectional=True)
            return Response(json.dumps(cookie), status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain", status=500, mimetype="application/json")


class ChainVnfDcStackInterfaces(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs):

        # search for real names
        real_names = self._findNames(src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs)
        if type(real_names) is not tuple:
            # something went wrong
            return real_names

        container_src, container_dst, interface_src, interface_dst = real_names

        try:
            cookie = self.api.manage.network_action_start(container_src, container_dst, vnf_src_interface=interface_src,
                                                          vnf_dst_interface=interface_dst, bidirectional=True)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as e:
            logging.exception(u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain", status=500, mimetype="application/json")

    def delete(self, src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs):

        # search for real names
        real_names = self._findNames(src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs)
        if type(real_names) is not tuple:
            # something went wrong, real_names is a Response object
            return real_names

        container_src, container_dst, interface_src, interface_dst = real_names

        try:
            cookie = self.api.manage.network_action_stop(container_src, container_dst, vnf_src_interface=interface_src,
                                                         vnf_dst_interface=interface_dst, bidirectional=True)
            return Response(json.dumps(cookie), status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain", status=500, mimetype="application/json")

    # Tries to find real container and interface names according to heat template names
    # Returns a tuple of 4 or a Response object
    def _findNames(self, src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs):
        # search for datacenters
        if src_dc not in self.api.manage.net.dcs or dst_dc not in self.api.manage.net.dcs:
            return Response(u"At least one DC does not exist", status=500, mimetype="application/json")
        dc_src = self.api.manage.net.dcs[src_dc]
        dc_dst = self.api.manage.net.dcs[dst_dc]
        # search for related OpenStackAPIs
        api_src = None
        api_dst = None
        from openstack_api_endpoint import OpenstackApiEndpoint
        for api in OpenstackApiEndpoint.dc_apis:
            if api.compute.dc == dc_src:
                api_src = api
            if api.compute.dc == dc_dst:
                api_dst = api
        if api_src is None or api_dst is None:
            return Response(u"At least one OpenStackAPI does not exist", status=500, mimetype="application/json")
        # search for stacks
        stack_src = None
        stack_dst = None
        for stack in api_src.compute.stacks.values():
            if stack.stack_name == src_stack:
                stack_src = stack
        for stack in api_dst.compute.stacks.values():
            if stack.stack_name == dst_stack:
                stack_dst = stack
        if stack_src is None or stack_dst is None:
            return Response(u"At least one Stack does not exist", status=500, mimetype="application/json")
        # search for servers
        server_src = None
        server_dst = None
        for server in stack_src.servers.values():
            if server.template_name == src_vnf:
                server_src = server
                break
        for server in stack_dst.servers.values():
            if server.template_name == dst_vnf:
                server_dst = server
                break
        if server_src is None or server_dst is None:
            return Response(u"At least one VNF does not exist", status=500, mimetype="application/json")

        container_src = server_src.name
        container_dst = server_dst.name

        # search for ports
        port_src = None
        port_dst = None
        if src_intfs in server_src.port_names:
            port_src = stack_src.ports[src_intfs]
        if dst_intfs in server_dst.port_names:
            port_dst = stack_dst.ports[dst_intfs]
        if port_src is None or port_dst is None:
            return Response(u"At least one Port does not exist", status=500, mimetype="application/json")

        interface_src = port_src.intf_name
        interface_dst = port_dst.intf_name

        return container_src, container_dst, interface_src, interface_dst


class BalanceHost(Resource):
    '''
     Handles requests at "/v1/lb/<vnf_src_name>/<vnf_src_interface>"
     and will set up or delete Load Balancers.
    '''

    def __init__(self, api):
        self.api = api

    def post(self, vnf_src_name, vnf_src_interface):
        '''
        Will set up a Load balancer behind an interface at a specified vnf
        We need both to avoid naming conflicts as interface names are not unique
        type: ALL | SELECT | FF, default is ALL
        Post data is in this format:
        {"dst_vnf_interfaces": {"dc1_man_serv0": "port-cp0-man",
        "dc2_man_serv0": "port-cp0-man","dc2_man_serv1": "port-cp1-man"}, "type": "ALL"}
        and specifies the balanced nodes
        :param vnf_src_name:
        :param vnf_src_interface:
        :return: flask Response
        '''
        req = request.json
        if req is None or len(req) == 0:
            return Response(u"You have to specify destination vnfs via the POST data.",
                            status=500, mimetype="application/json")
        net = self.api.manage.net
        src_sw_inport_nr = 0
        dest_intfs_mapping = req.get('dst_vnf_interfaces', dict())

        #use all as default, as it is easiest for debugging purposes
        # ryu expects the type to be uppercase
        type = req.get('type', "ALL").upper()
        dest_vnf_outport_nrs = list()

        # find the switch belonging to the source interface, as well as the inport nr
        for connected_sw in self.api.manage.net.DCNetwork_graph.neighbors(vnf_src_name):
            link_dict = self.api.manage.net.DCNetwork_graph[vnf_src_name][connected_sw]
            for link in link_dict:
                if link_dict[link]['src_port_name'] == vnf_src_interface:
                    src_sw = connected_sw
                    src_sw_inport_nr = link_dict[link]['dst_port_nr']
                    break

        if src_sw is None or src_sw_inport_nr == 0:
            return Response(u"Source VNF or interface can not be found." % vnf_src_name,
                            status=404, mimetype="application/json")

        # get all target interface outport numbers
        for vnf_name in dest_intfs_mapping:
            if vnf_name not in net.DCNetwork_graph:
                return Response(u"Target VNF %s is not known." % vnf_name,
                                status=404, mimetype="application/json")
            for connected_sw in net.DCNetwork_graph.neighbors(vnf_name):
                link_dict = net.DCNetwork_graph[vnf_name][connected_sw]
                for link in link_dict:
                    if link_dict[link]['src_port_name'] == dest_intfs_mapping[vnf_name]:
                        dest_vnf_outport_nrs.append(int(link_dict[link]['dst_port_nr']))

        # setup group table for load balancing on the first switch
        group_add = dict()
        # get first switch
        if vnf_src_interface not in self.api.manage.lb_flow_cookies:
            self.api.manage.lb_flow_cookies[vnf_src_interface] = list()

        group_add['dpid'] = int(net.getNodeByName(src_sw).dpid, 16)
        group_add['priority'] = 0
        group_add['type'] = type
        group_id = self.api.manage.get_flow_group(vnf_src_interface)
        group_add['group_id'] = group_id
        group_add['buckets'] = list()

        flows = list()
        # set up an initial flow that will set the LB group at the src interface
        flow = dict()
        flow['dpid'] = int(net.getNodeByName(src_sw).dpid, 16)
        flow['match'] = net._parse_match('in_port=%s' % src_sw_inport_nr)
        # cookie used by this flow
        cookie = self.api.manage.get_cookie()
        self.api.manage.lb_flow_cookies[vnf_src_interface].append(cookie)
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
        for dst_vnf_name in dest_intfs_mapping:
            path, src_sw, dst_sw = self.api.manage._get_path(vnf_src_name, dst_vnf_name)
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
            flow_cookie = self.api.manage.get_cookie()
            self.api.manage.network_action_start(dst_vnf_name, vnf_src_name,
                                                 vnf_src_interface=dest_intfs_mapping[dst_vnf_name],
                                                 vnf_dst_interface=vnf_src_interface, bidirectional=False,
                                                 cookie=flow_cookie)
            self.api.manage.lb_flow_cookies[vnf_src_interface].append(flow_cookie)

        # always create the group before adding the flow entries
        logging.debug("Setting up groupentry %s" % group_add)
        if net.controller == RemoteController:
            net.ryu_REST("stats/groupentry/add", data=group_add)
        else:
            self.api.manage.convert_ryu_to_ofctl(group_add, "add-group")

        for flow in flows:
            logging.debug("Setting up flowentry %s" % flow)
            if net.controller == RemoteController:
                net.ryu_REST('stats/flowentry/add', data=flow)
            else:
                self.api.manage.convert_ryu_to_ofctl(flow)

    def delete(self, vnf_src_name, vnf_src_interface):
        '''
        Will delete a load balancer that sits behind a specified interface at a vnf
        :param vnf_src_name:  the targeted vnf
        :param vnf_src_interface:  the interface behind which the load balancer is sitting
        :return: flask Response
        '''
        logging.debug("Deleting loadbalancer at %s: interface: %s", (vnf_src_name, vnf_src_interface))
        net = self.api.manage.net

        # check if both VNFs exist
        if vnf_src_name not in net:
            return Response(u"Source VNF or interface can not be found." % vnf_src_name,
                            status=404, mimetype="application/json")

        flows = list()
        # we have to call delete-group for each switch
        delete_group = list()
        group_id = self.api.manage.flow_groups[vnf_src_interface]
        for node in net.switches:
            for cookie in self.api.manage.lb_flow_cookies[vnf_src_interface]:
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
            if net.controller == RemoteController:
                net.ryu_REST('stats/flowentry/delete', data=flow)
            else:
                self.api.manage.convert_ryu_to_ofctl(flow, "del-flows")

        logging.debug("Deleting group with id %s" % group_id)
        for switch_del_group in delete_group:
            if net.controller == RemoteController:
                net.ryu_REST("stats/groupentry/delete", data=switch_del_group)
            else:
                self.api.manage.convert_ryu_to_ofctl(switch_del_group, "del-groups")

        # unmap groupid from the interface
        del self.api.manage.flow_groups[vnf_src_interface]
