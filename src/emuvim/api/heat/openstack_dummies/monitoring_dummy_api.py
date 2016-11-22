from flask_restful import Resource
from flask import Response, request
from emuvim.api.heat.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import logging
import json
import time


class MonitorDummyApi(BaseOpenstackDummy):
    def __init__(self, inc_ip, inc_port, compute):
        super(MonitorDummyApi, self).__init__(inc_ip, inc_port)
        self.compute = compute

        self.api.add_resource(MonitorVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(MonitorVnf, "/v1/monitor/<vnf_name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(MonitorVnfAbs, "/v1/monitor/abs/<vnf_name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(MonitorVnfDcStack, "/v1/monitor/<dc>/<stack>/<vnf_name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(Shutdown, "/shutdown")

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("MonitorDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False, threaded=True)


class Shutdown(Resource):
    def get(self):
        logging.debug(("%s is beeing shut down") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


class MonitorVersionsList(Resource):

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


class MonitorVnf(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, vnf_name):
        if len(vnf_name) < 3 or 'mn.' != vnf_name[:3]:
            vnf_name = 'mn.' + vnf_name
        if vnf_name[3:] not in self.api.compute.dc.net:
            return Response(u"MonitorAPI: VNF %s does not exist.\n" % (vnf_name[:3]),
                            status=500, mimetype="application/json")

        try:
            docker_id = self.api.compute.docker_container_id(vnf_name)
            out_dict = dict()
            out_dict.update(self.api.compute.docker_cpu(docker_id))
            out_dict['MEM_used'] = self.api.compute.docker_mem_used(docker_id)
            out_dict['MEM_limit'] = self.api.compute.docker_max_mem(docker_id)
            out_dict['MEM_%'] = float(out_dict['MEM_used']) / float(out_dict['MEM_limit'])
            out_dict.update(self.api.compute.docker_net_io(docker_id))
            out_dict['BLOCK_read'] = self.api.compute.docker_block_r(docker_id)
            out_dict['BLOCK_write'] = self.api.compute.docker_block_w(docker_id)
            out_dict['PIDS'] = self.api.compute.docker_PIDS(docker_id)
            out_dict['SYS_time'] = int(time.time() * 1000000000)

            return Response(json.dumps(out_dict)+'\n', status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error getting monitoring informations.\n %s" % (__name__, e))
            return Response(u"Error getting monitoring informations.\n", status=500, mimetype="application/json")


class MonitorVnfAbs(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, vnf_name):
        if len(vnf_name) < 3 or 'mn.' != vnf_name[:3]:
            vnf_name = 'mn.' + vnf_name
        if vnf_name[3:] not in self.api.compute.dc.net:
            return Response(u"MonitorAPI: VNF %s does not exist\n", status=500, mimetype="application/json")

        try:
            docker_id = self.api.compute.docker_container_id(vnf_name)
            out_dict = dict()
            out_dict.update(self.api.compute.docker_abs_cpu(docker_id))
            out_dict['MEM_used'] = self.api.compute.docker_mem_used(docker_id)
            out_dict['MEM_limit'] = self.api.compute.docker_max_mem(docker_id)
            out_dict['MEM_%'] = float(out_dict['MEM_used']) / float(out_dict['MEM_limit'])
            out_dict.update(self.api.compute.docker_net_io(docker_id))
            out_dict['BLOCK_read'] = self.api.compute.docker_block_r(docker_id)
            out_dict['BLOCK_write'] = self.api.compute.docker_block_w(docker_id)
            out_dict['PIDS'] = self.api.compute.docker_PIDS(docker_id)
            out_dict['SYS_time'] = int(time.time() * 1000000000)

            return Response(json.dumps(out_dict)+'\n', status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error getting monitoring informations.\n %s" % (__name__, e))
            return Response(u"Error getting monitoring informations.\n", status=500, mimetype="application/json")

class MonitorVnfDcStack(Resource):

    def __init__(self, api):
        self.api = api

    def get(self, dc, stack, vnf_name):

        # search for real name
        vnf_name = self._findName(dc,stack,vnf_name)

        if type(vnf_name) is not str:
            # something went wrong, vnf_name is a Response object
            return vnf_name

        if len(vnf_name) < 3 or 'mn.' != vnf_name[:3]:
            vnf_name = 'mn.' + vnf_name

        try:
            docker_id = self.api.compute.docker_container_id(vnf_name)
            out_dict = dict()
            out_dict['CPU_%'] = self.api.compute.docker_cpu(docker_id)
            out_dict['MEM_used'] = self.api.compute.docker_mem_used(docker_id)
            out_dict['MEM_limit'] = self.api.compute.docker_max_mem(docker_id)
            out_dict['MEM_%'] = float(out_dict['MEM_used']) / float(out_dict['MEM_limit'])
            out_dict.update(self.api.compute.docker_net_io(docker_id))
            out_dict['BLOCK_read'] = self.api.compute.docker_block_r(docker_id)
            out_dict['BLOCK_write'] = self.api.compute.docker_block_w(docker_id)
            out_dict['PIDS'] = self.api.compute.docker_PIDS(docker_id)
            out_dict['SYS_time'] = int(time.time() * 1000000000)

            return Response(json.dumps(out_dict)+'\n', status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error getting monitoring informations.\n %s" % (__name__, e))
            return Response(u"Error getting monitoring informations.\n", status=500, mimetype="application/json")

    # Tries to find real container name according to heat template names
    # Returns a string or a Response object
    def _findName(self, dc, stack, vnf):
        # search for datacenters
        if dc not in self.api.manage.net.dcs:
            return Response(u"DC does not exist", status=500, mimetype="application/json")
        dc_real = self.api.manage.net.dcs[dc]
        # search for related OpenStackAPIs
        api_real = None
        from ..openstack_api_endpoint import OpenstackApiEndpoint
        for api in OpenstackApiEndpoint.dc_apis:
            if api.compute.dc == dc_real:
                api_real = api
        if api_real is None:
            return Response(u"OpenStackAPI does not exist", status=500, mimetype="application/json")
        # search for stacks
        stack_real = None
        for stackObj in api_real.compute.stacks.values():
            if stackObj.stack_name == stack:
                stack_real = stackObj
        if stack_real is None:
            return Response(u"Stack does not exist", status=500, mimetype="application/json")
        # search for servers
        server_real = None
        for server in stack_real.servers.values():
            if server.template_name == vnf:
                server_real = server
                break
        if server_real is None:
            return Response(u"VNF does not exist", status=500, mimetype="application/json")

        container_real = server_real.name

        return container_real
