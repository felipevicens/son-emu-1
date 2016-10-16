import logging

logging.basicConfig(level=logging.DEBUG)


class OpenstackNet:
    def __init__(self, dc_network=None):
        self.net = dc_network

    def network_action_start(self, vnf_src_name, vnf_dst_name, **kwargs):
        try:
            c = self.net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=kwargs.get('vnf_src_interface'),
                vnf_dst_interface=kwargs.get('vnf_dst_interface'),
                cmd='add-flow',
                weight=kwargs.get('weight'),
                match=kwargs.get('match'),
                bidirectional=kwargs.get('bidirectional'),
                cookie=kwargs.get('cookie'))
            return str(c)
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def network_action_stop(self, vnf_src_name, vnf_dst_name, **kwargs):
        # call DCNetwork method, not really datacenter specific API for now...
        # provided dc name needs to be part of API endpoint
        # no check if vnfs are really connected to this datacenter...
        logging.debug("RPC CALL: network chain stop")
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
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message