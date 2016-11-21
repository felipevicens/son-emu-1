from flask import Flask
from flask_restful import Api, Resource
from flask import Response, request
import logging
import json


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
        self.api.add_resource(LoadBalancer, "/v1/lb/<name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(BalanceHost, "/v1/lb/<vnf_src_interface>",
                              resource_class_kwargs={'api': self})

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("ChainDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class ChainVersionsList(Resource):
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
    def __init__(self, api):
        self.api = api

    def put(self, src_vnf, dst_vnf):
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
    def __init__(self, api):
        self.api = api

    def put(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
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


class LoadBalancer(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, name):
        pass


class BalanceHost(Resource):
    def __init__(self, api):
        self.api = api

    def post(self, vnf_src_interface):
        #TODO: not done yet!
        req = request.json
        if req is None or len(req) == 0:
            return Response(u"You have to specify destination vnfs via the POST data.",
                            status=500, mimetype="application/json")
        vnf_src_name = ""
        src_sw_inport_nr = 0
        dest_intfs_names = req.get('dst_vnf_interfaces', list())
        dest_vnf_outport_nrs = set()

        for node in self.api.manage.net.values():
            for intfs in node.intfList():
                if intfs.name == vnf_src_interface:
                    vnf_src_name = node.name


        for connected_sw in self.api.manage.net.DCNetwork_graph:
            link_dict = self.api.manage.net.DCNetwork_graph[vnf_src_name][connected_sw]
            for link in link_dict:
                if link_dict[link]['src_port_name'] == vnf_src_interface:
                    src_sw_inport_nr = link_dict[link]['dst_port_nr']



                print link_dict[link]

                for dest_vnf_intfs in dest_intfs_names:
                   # print link_dict[link]['src_port_name']
                   # print dest_vnf_intfs
                    if link_dict[link]['src_port_name'] == dest_vnf_intfs:
                        dest_vnf_outport_nrs.add(link_dict[link]['dst_port_nr'])


        print src_sw_inport_nr
        print "Output %s" % " ".join(dest_vnf_outport_nrs)
        #self.api.manage.net.ryu_REST()
        pass
