import logging
import chain_api
import threading

logging.basicConfig(level=logging.DEBUG)


class OpenstackManage(object):
    def __init__(self, ip = "0.0.0.0", port = 4000):
        self.endpoints = dict()
        self.cookies = set()
        self.cookies.add(0)
        self.ip = ip
        self.port = port
        self.net = None

        # we want one global chain api. this should not be datacenter dependent!
        chain = chain_api.ChainApi(ip, port, self)
        thread = threading.Thread(target=chain._start_flask, args=())
        thread.daemon = True
        thread.name = chain.__class__
        thread.start()
        self.add_endpoint(chain)

    def add_endpoint(self, ep):
        key = "%s:%s" % (ep.ip, ep.port)
        self.endpoints[key] = ep
        ep.manage = self

    def network_action_start(self, vnf_src_name, vnf_dst_name, **kwargs):
        try:
            cookie = kwargs.get('cookie',max(self.cookies)+1)
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