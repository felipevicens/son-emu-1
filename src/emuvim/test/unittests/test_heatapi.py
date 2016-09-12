"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""

"""
Test suite to automatically test emulator REST API endpoints.
"""

import time
import unittest
from emuvim.test.api_base_heat import ApiBaseHeat
import subprocess
from emuvim.dcemulator.node import EmulatorCompute
import ast
import requests
import simplejson as json


class testRestApi(ApiBaseHeat):
    """
    Tests to check the REST API endpoints of the emulator.
    """

    def setUp(self):
        # create network
        self.createNet(nswitches=0, ndatacenter=2, nhosts=2, ndockers=0)

        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[1])
        self.net.addLink(self.dc[0], self.dc[1])

        # start api
        self.startApi()

        # start Mininet network
        self.startNet()

    def testCreateStack(self):
        print('->>>>>>> testCreateStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')

        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        data = {"template": {"heat_template_version": "2015-04-30", "resources": {"tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Net", "properties": {"name": "tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "tcpdump-vnf:vdu01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Nova::Server", "properties": {"flavor": "m1.small", "networks": [{"port": {"get_resource": "tcpdump-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, {"port": {"get_resource": "tcpdump-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, {"port": {"get_resource": "tcpdump-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}], "image": "ubuntu:trusty", "name": "tcpdump-vnf:vdu01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "tcpdump-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Subnet", "properties": {"cidr": "192.0.0.48/29", "gateway_ip": "192.0.0.49", "name": "tcpdump-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "tcpdump-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "firewall-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "firewall-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "sonata-demo:mgmt:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "iperf-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Net", "properties": {"name": "iperf-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "firewall-vnf:vdu01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Nova::Server", "properties": {"flavor": "m1.small", "networks": [{"port": {"get_resource": "firewall-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, {"port": {"get_resource": "firewall-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, {"port": {"get_resource": "firewall-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}], "image": "ubuntu:trusty", "name": "firewall-vnf:vdu01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "firewall-vnf:vnf:input:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::RouterInterface", "properties": {"router": {"get_resource": "sonata-demo:iperf-2-firewall:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}, "subnet": {"get_resource": "firewall-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "floating:iperf-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::FloatingIP", "properties": {"floating_network_id": "decd89e2-1681-427e-ac24-6e9f1abb1715", "port_id": {"get_resource": "iperf-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "firewall-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Subnet", "properties": {"cidr": "192.0.0.32/29", "gateway_ip": "192.0.0.33", "name": "firewall-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "firewall-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "firewall-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Subnet", "properties": {"cidr": "192.0.0.24/29", "gateway_ip": "192.0.0.25", "name": "firewall-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "firewall-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "floating:firewall-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::FloatingIP", "properties": {"floating_network_id": "decd89e2-1681-427e-ac24-6e9f1abb1715", "port_id": {"get_resource": "firewall-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "sonata-demo:mgmt:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Net", "properties": {"name": "sonata-demo:mgmt:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "sonata-demo:iperf-2-firewall:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Router", "properties": {"name": "sonata-demo:iperf-2-firewall:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "firewall-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "firewall-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "firewall-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "firewall-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "firewall-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "firewall-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "iperf-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "iperf-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "iperf-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "sonata-demo:firewall-2-tcpdump:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Router", "properties": {"name": "sonata-demo:firewall-2-tcpdump:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "firewall-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Net", "properties": {"name": "firewall-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "iperf-vnf:vnf:output:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::RouterInterface", "properties": {"router": {"get_resource": "sonata-demo:iperf-2-firewall:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}, "subnet": {"get_resource": "iperf-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "tcpdump-vnf:vnf:input:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::RouterInterface", "properties": {"router": {"get_resource": "sonata-demo:firewall-2-tcpdump:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}, "subnet": {"get_resource": "tcpdump-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "firewall-vnf:vnf:output:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::RouterInterface", "properties": {"router": {"get_resource": "sonata-demo:firewall-2-tcpdump:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}, "subnet": {"get_resource": "firewall-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "iperf-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Net", "properties": {"name": "iperf-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "iperf-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "iperf-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "iperf-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "iperf-vnf:vdu01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Nova::Server", "properties": {"flavor": "m1.small", "networks": [{"port": {"get_resource": "iperf-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, {"port": {"get_resource": "iperf-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, {"port": {"get_resource": "iperf-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}], "image": "ubuntu:trusty", "name": "iperf-vnf:vdu01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "tcpdump-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Net", "properties": {"name": "tcpdump-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "iperf-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Subnet", "properties": {"cidr": "192.0.0.16/29", "gateway_ip": "192.0.0.17", "name": "iperf-vnf:output:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "iperf-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "floating:tcpdump-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::FloatingIP", "properties": {"floating_network_id": "decd89e2-1681-427e-ac24-6e9f1abb1715", "port_id": {"get_resource": "tcpdump-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "tcpdump-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "tcpdump-vnf:vdu01:cp03:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "tcpdump-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "tcpdump-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "tcpdump-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "sonata-demo:mgmt:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "sonata-demo:mgmt:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Subnet", "properties": {"cidr": "192.0.0.0/29", "gateway_ip": "192.0.0.1", "name": "sonata-demo:mgmt:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "sonata-demo:mgmt:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "firewall-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Net", "properties": {"name": "firewall-vnf:output:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}, "tcpdump-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Subnet", "properties": {"cidr": "192.0.0.40/29", "gateway_ip": "192.0.0.41", "name": "tcpdump-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "iperf-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Subnet", "properties": {"cidr": "192.0.0.8/29", "gateway_ip": "192.0.0.9", "name": "iperf-vnf:input:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "iperf-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "iperf-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "iperf-vnf:vdu01:cp01:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "sonata-demo:mgmt:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "sonata-demo:mgmt:internal:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::RouterInterface", "properties": {"router": "20790da5-2dc1-4c7e-b9c3-a8d590517563", "subnet": {"get_resource": "sonata-demo:mgmt:subnet:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}, "tcpdump-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest": {"type": "OS::Neutron::Port", "properties": {"name": "tcpdump-vnf:vdu01:cp02:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest", "network": {"get_resource": "tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"}}}}}, "stack_name": "stack_no_1"}

        headers = {'Content-type': 'application/json'}
        r = requests.post(url, data=json.dumps(data), headers=headers)
        self.assertTrue(r.status_code == 200)
"""


        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 3)
        self.assertTrue(len(self.net.hosts) == 5)
        self.assertTrue(len(self.net.switches) == 2)

        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 2)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)
        self.assertTrue(isinstance(self.dc[0].listCompute()[0], EmulatorCompute))
        self.assertTrue(isinstance(self.dc[0].listCompute()[1], EmulatorCompute))
        self.assertTrue(isinstance(self.dc[1].listCompute()[0], EmulatorCompute))
        self.assertTrue(self.dc[0].listCompute()[1].name == "vnf1")
        self.assertTrue(self.dc[0].listCompute()[0].name == "vnf2")
        self.assertTrue(self.dc[1].listCompute()[0].name == "vnf3")

        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.dc[0].listCompute()[1], self.dc[0].listCompute()[0]]) <= 0.0)
        self.assertTrue(self.net.ping([self.dc[0].listCompute()[0], self.dc[1].listCompute()[0]]) <= 0.0)
        self.assertTrue(self.net.ping([self.dc[1].listCompute()[0], self.dc[0].listCompute()[1]]) <= 0.0)

        print('network add vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("/media/sf_son-emu/src/emuvim/cli/son-emu-cli network add -src vnf1 -dst vnf2 -b -c 10", shell=True)
        print('network remove vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("/media/sf_son-emu/src/emuvim/cli/son-emu-cli network remove -src vnf1 -dst vnf2 -b", shell=True)

        print('>>>>> checking --> son-emu-cli compute stop -d datacenter0 -n vnf2 ->>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("/media/sf_son-emu/src/emuvim/cli/son-emu-cli compute stop -d datacenter0 -n vnf2", shell=True)

        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 2)
        self.assertTrue(len(self.net.hosts) == 4)
        self.assertTrue(len(self.net.switches) == 2)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 1)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)

        print('>>>>> checking --> son-emu-cli compute list ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("/media/sf_son-emu/src/emuvim/cli/son-emu-cli compute list", shell=True)
        output = subprocess.check_output("/media/sf_son-emu/src/emuvim/cli/son-emu-cli compute list", shell=True)

        # check datacenter list result
        self.assertTrue("datacenter0" in output)

        print('>>>>> checking --> son-emu-cli compute status -d datacenter0 -n vnf1 ->>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("/media/sf_son-emu/src/emuvim/cli/son-emu-cli compute status -d datacenter0 -n vnf1", shell=True)
        output = subprocess.check_output("/media/sf_son-emu/src/emuvim/cli/son-emu-cli compute status -d datacenter0 -n vnf1", shell=True)
        output = ast.literal_eval(output)

        # check compute status result
        self.assertTrue(output["name"] == "vnf1")
        self.assertTrue(output["state"]["Running"])

        print('>>>>> checking --> son-emu-cli datacenter list ->>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("/media/sf_son-emu/src/emuvim/cli/son-emu-cli datacenter list", shell=True)
        output = subprocess.check_output("/media/sf_son-emu/src/emuvim/cli/son-emu-cli datacenter list", shell=True)

        # check datacenter list result

        self.assertTrue("datacenter0" in output)

        print('->>>>> checking --> son-emu-cli datacenter status -d datacenter0 ->>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("/media/sf_son-emu/src/emuvim/cli/son-emu-cli datacenter status -d datacenter0", shell=True)
        output = subprocess.check_output("/media/sf_son-emu/src/emuvim/cli/son-emu-cli datacenter status -d datacenter0", shell=True)

        # check datacenter status result
        self.assertTrue("datacenter0" in output)

        #self.stopNet()
"""

if __name__ == '__main__':
    unittest.main()
