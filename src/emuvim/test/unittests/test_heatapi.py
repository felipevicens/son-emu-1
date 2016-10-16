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

    def testNovaDummy(self):
        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open("test_heatapi_template_create_stack.json").read()
        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        requests.post(url, data=json.dumps(json.loads(test_heatapi_template_create_stack)),
                      headers=headers)

        print('->>>>>>> testNovaListVersions ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/"
        listapiversionnovaresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionnovaresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionnovaresponse.content)["versions"][0]["id"], "v2.1")
        print(" ")

        print('->>>>>>> testNovaVersionShow ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla"
        listapiversion21novaresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversion21novaresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversion21novaresponse.content)["version"]["id"], "v2.1")
        print(" ")

        print('->>>>>>> testNovaVersionListServerAPIs ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers"
        listserverapisnovaresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverapisnovaresponse.status_code, 200)
        self.assertNotEqual(json.loads(listserverapisnovaresponse.content)["servers"][0]["name"], "")
        print(" ")

        print('->>>>>>> testNovaVersionListServerAPIsDetailed ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers/detail"
        listserverapisdetailedresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverapisdetailedresponse.status_code, 200)
        self.assertNotEqual(json.loads(listserverapisdetailedresponse.content)["servers"][0]["name"], "")
        print(" ")

        #print('->>>>>>> testNovaShowServerDetails ->>>>>>>>>>>>>>>')
        #print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        #url = "http://0.0.0.0:8774/v2.1/id_bla/servers/%s" % (json.loads(listserverapisdetailedresponse.content)["servers"][0]["id"])
        #listserverdetailsresponse = requests.get(url, headers=headers)
        #self.assertEqual(listserverdetailsresponse.status_code, 200)
        #print (listserverdetailsresponse.content)
        #self.assertEqual(json.loads(listserverdetailsresponse.content)["server"], "")
        #print(" ")

        print('->>>>>>> testNovaListFlavors ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/flavors"
        listflavorsresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsresponse.status_code, 200)
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][0]["name"], ["m1.nano", "m1.tiny", "m1.micro"])
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][1]["name"], ["m1.nano", "m1.tiny", "m1.micro"])
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][2]["name"], ["m1.nano", "m1.tiny", "m1.micro"])
        print(" ")

        print('->>>>>>> testNovaListFlavorsDetail ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/flavors/detail"
        listflavorsdetailresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsdetailresponse.status_code, 200)
        print (listflavorsdetailresponse.content)
        self.assertIn(json.loads(listflavorsdetailresponse.content)["flavors"][0]["name"], ["m1.nano", "m1.tiny", "m1.micro"])
        self.assertIn(json.loads(listflavorsdetailresponse.content)["flavors"][1]["name"], ["m1.nano", "m1.tiny", "m1.micro"])
        self.assertIn(json.loads(listflavorsdetailresponse.content)["flavors"][2]["name"], ["m1.nano", "m1.tiny", "m1.micro"])
        print(" ")



"""
    def testNeutronDummy(self):
        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open("test_heatapi_template_create_stack.json").read()
        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        requests.post(url, data=json.dumps(json.loads(test_heatapi_template_create_stack)),
                                            headers=headers)
        # test_heatapi_keystone_get_token = open("test_heatapi_keystone_get_token.json").read()
        print(" ")

        print('->>>>>>> testNeutronListVersions ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/"
        listapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionstackresponse.content)["versions"][0]["id"], "v2.0")
        print(" ")

        print('->>>>>>> testNeutronShowAPIv2.0 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0"
        listapiversionv20response = requests.get(url, headers=headers)
        self.assertEqual(listapiversionv20response.status_code, 200)
        self.assertEqual(json.loads(listapiversionv20response.content)["resources"][0]["name"], "subnet")
        self.assertEqual(json.loads(listapiversionv20response.content)["resources"][1]["name"], "network")
        self.assertEqual(json.loads(listapiversionv20response.content)["resources"][2]["name"], "ports")
        print(" ")

        print('->>>>>>> testNeutronListNetworks ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks"
        listnetworksesponse = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse.content)["networks"][0]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> testNeutronCreateNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks"
        createnetworkresponse = requests.post(url, data='{"network": {"name": "sample_network","admin_state_up": true}}', headers=headers)
        self.assertEqual(createnetworkresponse.status_code, 201)
        self.assertEqual(json.loads(createnetworkresponse.content)["network"]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> testNeutronCreateNetworkWithExistingName 400->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks"
        createnetworkresponsefailure = requests.post(url,data='{"network": {"name": "sample_network","admin_state_up": true}}',headers=headers)
        self.assertEqual(createnetworkresponsefailure.status_code, 400)
        print(" ")

        print('->>>>>>> testNeutronUpdateNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks/%s" % (json.loads(createnetworkresponse.content)["network"]["id"])
        updatenetworkresponse = requests.put(url, data='{"network": {"name": "sample_network_new_name","admin_state_up": true}}' , headers=headers)
        self.assertEqual(updatenetworkresponse.status_code, 200)
        self.assertEqual(json.loads(updatenetworkresponse.content)["network"]["name"], "sample_network_new_name")
        print(" ")

        print('->>>>>>> testNeutronListSubnets ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        listsubnetsesponse = requests.get(url, headers=headers)
        self.assertEqual(listsubnetsesponse.status_code, 200)
        self.assertIn("subnet", json.loads(listsubnetsesponse.content)["subnets"][0]["name"])
        print(" ")

        print('->>>>>>> testNeutronShowSubnet->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets/%s" % (json.loads(listsubnetsesponse.content)["subnets"][0]["id"])
        showsubnetsesponse = requests.get(url, headers=headers)
        self.assertEqual(showsubnetsesponse.status_code, 200)
        self.assertIn("subnet", json.loads(showsubnetsesponse.content)["subnet"]["name"])
        print(" ")

        print('->>>>>>> testNeutronCreateSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        createsubnetdata = '{"subnet": {"name": "new_subnet", "network_id": "%s","ip_version": 4,"cidr": "10.0.0.1/24"} }' % (json.loads(createnetworkresponse.content)["network"]["id"])
        createsubnetresponse = requests.post(url, data=createsubnetdata, headers=headers)
        self.assertEqual(createsubnetresponse.status_code, 201)
        self.assertEqual(json.loads(createsubnetresponse.content)["subnet"]["name"], "new_subnet")
        print(" ")

        print('->>>>>>> testNeutronUpdateSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets/%s" % (json.loads(createsubnetresponse.content)["subnet"]["id"])
        updatesubnetdata = '{"subnet": {"name": "new_subnet_new_name"} }'
        updatesubnetresponse = requests.put(url, data=updatesubnetdata, headers=headers)
        self.assertEqual(updatesubnetresponse.status_code, 200)
        self.assertEqual(json.loads(updatesubnetresponse.content)["subnet"]["name"], "new_subnet_new_name")
        print(" ")



        print('->>>>>>> testNeutronListPorts ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports"
        listportsesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsesponse.status_code, 200)
        self.assertEqual(json.loads(listportsesponse.content)["ports"][0]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> testNeutronShowPort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports/%s" % (json.loads(listportsesponse.content)["ports"][0]["id"])
        showportresponse = requests.get(url, headers=headers)
        self.assertEqual(showportresponse.status_code, 200)
        self.assertEqual(json.loads(showportresponse.content)["port"]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> testNeutronCreatePort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports"
        createportdata = '{"port": {"name": "new_port", "network_id": "%s"} }' % (json.loads(createnetworkresponse.content)["network"]["id"])
        createportresponse = requests.post(url, data=createportdata, headers=headers)
        self.assertEqual(createportresponse.status_code, 201)
        self.assertEqual(json.loads(createportresponse.content)["port"]["name"], "new_port")
        print(" ")

        print('->>>>>>> testNeutronUpdatePort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports/%s" % (json.loads(createportresponse.content)["port"]["id"])
        updateportdata = '{"port": {"name": "new_port_new_name"} }'
        updateportresponse = requests.put(url, data=updateportdata, headers=headers)
        self.assertEqual(updateportresponse.status_code, 200)
        self.assertEqual(json.loads(updateportresponse.content)["port"]["name"], "new_port_new_name")
        print(" ")

        print('->>>>>>> testNeutronDeletePort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:9696/v2.0/ports/unknownid"
        righturl = "http://0.0.0.0:9696/v2.0/ports/%s" % (json.loads(createportresponse.content)["port"]["id"])
        deletewrongportresponse = requests.delete(wrongurl, headers=headers)
        deleterightportresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deletewrongportresponse.status_code, 404)
        self.assertEqual(deleterightportresponse.status_code, 204)
        print(" ")



        print('->>>>>>> testNeutronDeleteSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:9696/v2.0/subnets/unknownid"
        righturl = "http://0.0.0.0:9696/v2.0/subnets/%s" % (json.loads(createsubnetresponse.content)["subnet"]["id"])
        deletewrongsubnetresponse = requests.delete(wrongurl, headers=headers)
        deleterightsubnetresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deletewrongsubnetresponse.status_code, 404)
        self.assertEqual(deleterightsubnetresponse.status_code, 204)
        print(" ")

        print('->>>>>>> testNeutronDeleteNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:9696/v2.0/networks/unknownid"
        righturl = "http://0.0.0.0:9696/v2.0/networks/%s" % (json.loads(createnetworkresponse.content)["network"]["id"])
        deletewrongnetworkresponse = requests.delete(wrongurl, headers=headers)
        deleterightnetworkresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deletewrongnetworkresponse.status_code, 404)
        self.assertEqual(deleterightnetworkresponse.status_code, 204)
        print(" ")


    def testKeystomeDummy(self):
        headers = {'Content-type': 'application/json'}
        test_heatapi_keystone_get_token = open("test_heatapi_keystone_get_token.json").read()
        print(" ")

        print('->>>>>>> testKeystoneListVersions ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:5000/"
        listapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionstackresponse.content)["versions"]["values"][0]["id"], "v2.0")
        print(" ")

        print('->>>>>>> testKeystoneShowApiV2 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:5000/v2.0"
        showapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(showapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(showapiversionstackresponse.content)["version"]["id"], "v2.0")
        print(" ")

        print('->>>>>>> testKeystoneGetToken ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:5000/v2.0/tokens"
        gettokenstackresponse = requests.post(url, data=json.dumps(json.loads(test_heatapi_keystone_get_token)), headers=headers)
        self.assertEqual(gettokenstackresponse.status_code, 200)
        self.assertEqual(json.loads(gettokenstackresponse.content)["access"]["user"]["name"], "tenantName")
        print(" ")

    def testHeatDummy(self):
        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open("test_heatapi_template_create_stack.json").read()
        test_heatapi_template_update_stack = open("test_heatapi_template_update_stack.json").read()
        print(" ")

        print('->>>>>>> testHeatListAPIVersionsStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/"
        listapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionstackresponse.content)["versions"][0]["id"], "v1.0")
        print(" ")

        print('->>>>>>> testCreateStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        createstackresponse = requests.post(url, data=json.dumps(json.loads(test_heatapi_template_create_stack)), headers=headers)
        self.assertEqual(createstackresponse.status_code, 200)
        self.assertNotEqual(json.loads(createstackresponse.content)["stack"]["id"], "")
        print(" ")

        print('->>>>>>> testListStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        liststackresponse = requests.get(url, headers=headers)
        self.assertEqual(liststackresponse.status_code, 200)
        self.assertEqual(json.loads(liststackresponse.content)["stacks"][0]["stack_status"], "CREATE_COMPLETE")
        print(" ")


        print('->>>>>>> testShowStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123showStack/stacks/%s"% json.loads(createstackresponse.content)['stack']['id']
        liststackdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(liststackdetailsresponse.status_code, 200)
        self.assertEqual(json.loads(liststackdetailsresponse.content)["stack"]["stack_status"], "CREATE_COMPLETE")
        print(" ")

        print('->>>>>>> testUpdateStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123updateStack/stacks/%s"% json.loads(createstackresponse.content)['stack']['id']
        updatestackresponse = requests.put(url, data=json.dumps(json.loads(test_heatapi_template_update_stack)),
                                            headers=headers)
        self.assertEqual(updatestackresponse.status_code, 202)
        liststackdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(json.loads(liststackdetailsresponse.content)["stack"]["stack_status"], "UPDATE_COMPLETE")
        print(" ")

        print('->>>>>>> testDeleteStack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8004/v1/tenantabc123showStack/stacks/%s" % \
              json.loads(createstackresponse.content)['stack']['id']
        deletestackdetailsresponse = requests.delete(url, headers=headers)
        self.assertEqual(deletestackdetailsresponse.status_code, 204)
        print(" ")

"""





""""
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
