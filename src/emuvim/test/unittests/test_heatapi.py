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

    def testStack(self):
        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open("test_heatapi_template_create_stack.json").read()
        test_heatapi_template_update_stack = open("test_heatapi_template_update_stack.json").read()
        print(" ")

        print('->>>>>>> testHeatListAPIVersionsStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/"
        listapiversionstackresponse = requests.get(url, headers=headers)
        self.assertTrue(listapiversionstackresponse.status_code == 200)
        self.assertTrue(json.loads(listapiversionstackresponse.content)["versions"][0]["id"] == "v1.0")
        print(" ")

        print('->>>>>>> testCreateStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        createstackresponse = requests.post(url, data=json.dumps(json.loads(test_heatapi_template_create_stack)), headers=headers)
        self.assertTrue(createstackresponse.status_code == 200)
        self.assertTrue(json.loads(createstackresponse.content)["stack"]["id"] != "")
        print(" ")

        print('->>>>>>> testListStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        liststackresponse = requests.get(url, headers=headers)
        self.assertTrue(liststackresponse.status_code == 200)
        self.assertTrue(json.loads(liststackresponse.content)["stacks"][0]["stack_status"] == "CREATE_COMPLETE")
        print(" ")


        print('->>>>>>> testShowStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123showStack/stacks/%s"% json.loads(createstackresponse.content)['stack']['id']
        liststackdetailsresponse = requests.get(url, headers=headers)
        self.assertTrue(liststackdetailsresponse.status_code == 200)
        print(liststackdetailsresponse.content)
        self.assertTrue(json.loads(liststackdetailsresponse.content)["stack"]["stack_status"] == "CREATE_COMPLETE")
        print(" ")

        print('->>>>>>> testUpdateStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123updateStack/stacks/%s"% json.loads(createstackresponse.content)['stack']['id']
        updatestackresponse = requests.put(url, data=json.dumps(json.loads(test_heatapi_template_update_stack)),
                                            headers=headers)
        self.assertTrue(updatestackresponse.status_code == 202)
        liststackdetailsresponse = requests.get(url, headers=headers)
        self.assertTrue(json.loads(liststackdetailsresponse.content)["stack"]["stack_status"] == "UPDATE_COMPLETE")
        print(" ")

        print('->>>>>>> testDeleteStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123showStack/stacks/%s" % \
              json.loads(createstackresponse.content)['stack']['id']
        deletestackdetailsresponse = requests.delete(url, headers=headers)
        self.assertTrue(deletestackdetailsresponse.status_code == 204)
        print(" ")







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
