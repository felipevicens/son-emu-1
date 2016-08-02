import logging

logging.basicConfig(level=logging.DEBUG)


class HeatNet:
    def __init__(self):
        self.net = None

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