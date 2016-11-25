import logging
import chain_api
import threading
import networkx as nx

# force full debug logging everywhere for now
logging.getLogger().setLevel(logging.DEBUG)
class OpenstackManage(object):

    # openstackmanage is a singleton!
    __instance = None

    def __new__(cls):
        if OpenstackManage.__instance is None:
            OpenstackManage.__instance = object.__new__(cls)
        return OpenstackManage.__instance

    def __init__(self, ip = "0.0.0.0", port = 4000):
        self.endpoints = dict()
        self.cookies = set()
        self.cookies.add(0)
        self.ip = ip
        self.port = port
        self.net = None
        # to keep track which src_vnf(input port on the switch) handles a load balancer
        self.lb_flow_cookies = dict()
        # flow groups could be handled for each switch separately, but this global group counter should be easier to
        # debug and to maintain
        self.flow_groups = list()

        # we want one global chain api. this should not be datacenter dependent!
        if not hasattr(self,"chain"):
            self.chain = chain_api.ChainApi(ip, port, self)
        if not hasattr(self, "thread"):
            self.thread = threading.Thread(target=self.chain._start_flask, args=())
            self.thread.daemon = True
            self.thread.name = self.chain.__class__
            self.thread.start()

    def add_endpoint(self, ep):
        key = "%s:%s" % (ep.ip, ep.port)
        self.endpoints[key] = ep

    def get_cookie(self):
        cookie = int(max(self.cookies) +1)
        self.cookies.add(cookie)
        return cookie

    def get_flow_group(self):
        grp = int(len(self.flow_groups) + 1)
        self.flow_groups.append(grp)
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
        # modified version of the _chainAddFlow from emuvim.dcemulator.net
        src_sw = None
        dst_sw = None
        logging.debug("Find path from vnf %s to %s",
                  src_vnf, dst_vnf)

        for connected_sw in self.net.DCNetwork_graph.neighbors(src_vnf):
            link_dict = self.net.DCNetwork_graph[src_vnf][connected_sw]
            for link in link_dict:
                for intfs in self.net[src_vnf].intfs.values():
                    if (link_dict[link]['src_port_id'] == intfs.name or
                            link_dict[link]['src_port_name'] == intfs.name):  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                        # found the right link and connected switch
                        src_sw = connected_sw
                        break


        for connected_sw in self.net.DCNetwork_graph.neighbors(dst_vnf):
            link_dict = self.net.DCNetwork_graph[connected_sw][dst_vnf]
            for link in link_dict:
                for intfs in self.net[dst_vnf].intfs.values():
                    if link_dict[link]['dst_port_id'] == intfs.name or \
                            link_dict[link]['dst_port_name'] == intfs.name:  # Fix: we might also get interface names, e.g, from a son-emu-cli call
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

        logging.info("Path between {0} and {1}: {2}".format(src_vnf,dst_vnf, path))
        return path, src_sw, dst_sw