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

import os
import unittest
import requests
import simplejson as json

from emuvim.test.api_base_heat import ApiBaseHeat


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
        test_heatapi_template_create_stack = open(os.path.join(os.path.dirname(__file__), "test_heatapi_template_create_stack.json")).read()
        url = "http://0.0.0.0:8004/v1/tenantabc123/stacks"
        requests.post(url, data=json.dumps(json.loads(test_heatapi_template_create_stack)),
                      headers=headers)

        print('->>>>>>> testNovaListVersions ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/"
        listapiversionnovaresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionnovaresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionnovaresponse.content)["versions"][0]["id"], "v2.1")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)["versions"][0]["status"], "CURRENT")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)["versions"][0]["version"], "2.38")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)["versions"][0]["min_version"], "2.1")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)["versions"][0]["updated"], "2013-07-23T11:33:21Z")
        print(" ")

        print('->>>>>>> testNovaVersionShow ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla"
        listapiversion21novaresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversion21novaresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversion21novaresponse.content)["version"]["id"], "v2.1")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)["version"]["status"], "CURRENT")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)["version"]["version"], "2.38")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)["version"]["min_version"], "2.1")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)["version"]["updated"], "2013-07-23T11:33:21Z")
        print(" ")

        print('->>>>>>> testNovaVersionListServerAPIs ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers"
        listserverapisnovaresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverapisnovaresponse.status_code, 200)
        self.assertNotEqual(json.loads(listserverapisnovaresponse.content)["servers"][0]["name"], "")
        print(" ")

        print('->>>>>>> testNovaListFlavors ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/flavors"
        listflavorsresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsresponse.status_code, 200)
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][0]["name"], ["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][1]["name"], ["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][2]["name"], ["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        print(" ")

        print('->>>>>>> testNovaListFlavorsDetail ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/flavors/detail"
        listflavorsdetailresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsdetailresponse.status_code, 200)
        self.assertIn(json.loads(listflavorsdetailresponse.content)["flavors"][0]["name"],["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsdetailresponse.content)["flavors"][1]["name"],["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsdetailresponse.content)["flavors"][2]["name"],["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        print(" ")

        print('->>>>>>> testNovaListFlavorById ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/flavors/%s" % (json.loads(listflavorsdetailresponse.content)["flavors"][0]["name"])
        listflavorsbyidresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsbyidresponse.status_code, 200)
        self.assertEqual(json.loads(listflavorsbyidresponse.content)["flavor"]["id"], json.loads(listflavorsdetailresponse.content)["flavors"][0]["id"])
        print(" ")


        print('->>>>>>> testNovaListImages ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/images"
        listimagesresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagesresponse.status_code, 200)
        self.assertIn(json.loads(listimagesresponse.content)["images"][0]["name"],["google/cadvisor:latest", "ubuntu:trusty", "prom/pushgateway:latest"])
        self.assertIn(json.loads(listimagesresponse.content)["images"][1]["name"],["google/cadvisor:latest", "ubuntu:trusty", "prom/pushgateway:latest"])
        self.assertIn(json.loads(listimagesresponse.content)["images"][2]["name"],["google/cadvisor:latest", "ubuntu:trusty", "prom/pushgateway:latest"])
        print(" ")

        print('->>>>>>> testNovaListImagesDetails ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/images/detail"
        listimagesdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagesdetailsresponse.status_code, 200)
        self.assertIn(json.loads(listimagesdetailsresponse.content)["images"][0]["name"],["google/cadvisor:latest", "ubuntu:trusty", "prom/pushgateway:latest"])
        self.assertIn(json.loads(listimagesdetailsresponse.content)["images"][1]["name"],["google/cadvisor:latest", "ubuntu:trusty", "prom/pushgateway:latest"])
        self.assertIn(json.loads(listimagesdetailsresponse.content)["images"][2]["name"],["google/cadvisor:latest", "ubuntu:trusty", "prom/pushgateway:latest"])
        self.assertEqual(json.loads(listimagesdetailsresponse.content)["images"][0]["metadata"]["architecture"],"x86_64")
        print(" ")

        print('->>>>>>> testNovaListImageById ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/images/%s" % (json.loads(listimagesdetailsresponse.content)["images"][0]["id"])
        listimagebyidresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagebyidresponse.status_code, 200)
        self.assertEqual(json.loads(listimagebyidresponse.content)["image"]["id"],json.loads(listimagesdetailsresponse.content)["images"][0]["id"])
        print(" ")

        print('->>>>>>> testNovaListImageByNonExistendId ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/images/non_existing_id"
        listimagebynonexistingidresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagebynonexistingidresponse.status_code, 404)
        print(" ")

        #find ubintu id
        for image in json.loads(listimagesresponse.content)["images"]:
            if image["name"] == "ubuntu:trusty":
                ubuntu_image_id = image["id"]



        print('->>>>>>> testNovacreateServerInstance ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers"
        data = '{"server": {"name": "X", "flavorRef": "%s", "imageRef":"%s"}}' % (json.loads(listflavorsresponse.content)["flavors"][0]["id"], ubuntu_image_id)
        createserverinstance = requests.post(url, data=data, headers=headers)
        self.assertEqual(createserverinstance.status_code, 200)
        self.assertEqual(json.loads(createserverinstance.content)["server"]["image"]["id"], ubuntu_image_id)
        print(" ")

        print('->>>>>>> testNovacreateServerInstanceWithExistingName ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers"
        data = '{"server": {"name": "X", "flavorRef": "%s", "imageRef":"%s"}}' % (json.loads(listflavorsresponse.content)["flavors"][0]["id"], ubuntu_image_id)
        createserverinstance = requests.post(url, data=data, headers=headers)
        self.assertEqual(createserverinstance.status_code, 409)
        print(" ")

        print('->>>>>>> testNovaVersionListServerAPIsDetailed ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers/detail"
        listserverapisdetailedresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverapisdetailedresponse.status_code, 200)
        self.assertEqual(json.loads(listserverapisdetailedresponse.content)["servers"][0]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> testNovaShowServerDetails ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers/%s" % (json.loads(listserverapisdetailedresponse.content)["servers"][0]["id"])
        listserverdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverdetailsresponse.status_code, 200)
        print (listserverdetailsresponse.content)
        self.assertEqual(json.loads(listserverdetailsresponse.content)["server"]["flavor"]["links"][0]["rel"], "bookmark")
        print(" ")

        print('->>>>>>> testNovaShowNonExistingServerDetails ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:8774/v2.1/id_bla/servers/non_existing_server_id"
        listnonexistingserverdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(listnonexistingserverdetailsresponse.status_code, 404)
        print(" ")



    def testNeutronDummy(self):
        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open(os.path.join(os.path.dirname(__file__), "test_heatapi_template_create_stack.json")).read()
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
        listnetworksesponse1 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse1.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse1.content)["networks"][0]["status"], "ACTIVE")
        listNetworksId = json.loads(listnetworksesponse1.content)["networks"][0]["id"]
        listNetworksName = json.loads(listnetworksesponse1.content)["networks"][0]["name"]
        listNetworksId2 = json.loads(listnetworksesponse1.content)["networks"][1]["id"]
        print(" ")

        print('->>>>>>> testNeutronListNonExistingNetworks ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks?name=non_existent_network_name"
        listnetworksesponse2 = requests.get(url,headers=headers)
        self.assertEqual(listnetworksesponse2.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronListNetworksByName ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks?name=" + listNetworksName #tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest
        listnetworksesponse3 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse3.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse3.content)["networks"][0]["name"], listNetworksName)
        print(" ")

        print('->>>>>>> testNeutronListNetworksById ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks?id=" + listNetworksId  # tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest
        listnetworksesponse4 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse4.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse4.content)["networks"][0]["id"], listNetworksId)
        print(" ")

        print('->>>>>>> testNeutronListNetworksByMultipleIds ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks?id=" + listNetworksId + "&id="+ listNetworksId2 # tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest
        listnetworksesponse5 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse5.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse5.content)["networks"][0]["id"], listNetworksId)
        self.assertEqual(json.loads(listnetworksesponse5.content)["networks"][1]["id"], listNetworksId2)
        print(" ")

        print('->>>>>>> testNeutronShowNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks/"+listNetworksId
        shownetworksesponse = requests.get(url, headers=headers)
        self.assertEqual(shownetworksesponse.status_code, 200)
        self.assertEqual(json.loads(shownetworksesponse.content)["network"]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> testNeutronShowNetworkNonExistendNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks/non_existent_network_id"
        shownetworksesponse2 = requests.get(url, headers=headers)
        self.assertEqual(shownetworksesponse2.status_code, 404)
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
        updatenetworkresponse = requests.put(url, data='{"network": {"status": "ACTIVE", "admin_state_up":true, "tenant_id":"abcd123", "name": "sample_network_new_name", "shared":false}}' , headers=headers)
        self.assertEqual(updatenetworkresponse.status_code, 200)
        self.assertEqual(json.loads(updatenetworkresponse.content)["network"]["name"], "sample_network_new_name")
        self.assertEqual(json.loads(updatenetworkresponse.content)["network"]["tenant_id"], "abcd123")
        print(" ")

        print('->>>>>>> testNeutronUpdateNonExistingNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/networks/non-existing-name123"
        updatenetworkresponse = requests.put(url, data='{"network": {"name": "sample_network_new_name"}}', headers=headers)
        self.assertEqual(updatenetworkresponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronListSubnets ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        listsubnetsresponse = requests.get(url, headers=headers)
        listSubnetName = json.loads(listsubnetsresponse.content)["subnets"][0]["name"]
        listSubnetId = json.loads(listsubnetsresponse.content)["subnets"][0]["id"]
        listSubnetId2 = json.loads(listsubnetsresponse.content)["subnets"][1]["id"]
        self.assertEqual(listsubnetsresponse.status_code, 200)
        self.assertIn("subnet", listSubnetName)
        print(" ")

        print('->>>>>>> testNeutronListSubnetsByName ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets?name="+listSubnetName
        listsubnetByNameresponse = requests.get(url, headers=headers)
        self.assertEqual(listsubnetByNameresponse.status_code, 200)
        self.assertIn("subnet", json.loads(listsubnetByNameresponse.content)["subnets"][0]["name"])
        print(" ")

        print('->>>>>>> testNeutronListSubnetsById ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets?id=" + listSubnetId
        listsubnetsbyidresponse = requests.get(url, headers=headers)
        self.assertEqual(listsubnetsbyidresponse.status_code, 200)
        self.assertIn("subnet", json.loads(listsubnetsbyidresponse.content)["subnets"][0]["name"])
        print(" ")

        print('->>>>>>> testNeutronListSubnetsByMultipleId ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets?id=" + listSubnetId +"&id="+listSubnetId2
        listsubnetsbymultipleidsresponse = requests.get(url, headers=headers)
        self.assertEqual(listsubnetsbymultipleidsresponse.status_code, 200)
        self.assertIn("subnet", json.loads(listsubnetsbymultipleidsresponse.content)["subnets"][0]["name"])
        print(" ")



        print('->>>>>>> testNeutronShowSubnet->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets/%s" % (json.loads(listsubnetsresponse.content)["subnets"][0]["id"])
        showsubnetsresponse = requests.get(url, headers=headers)
        self.assertEqual(showsubnetsresponse.status_code, 200)
        self.assertIn("subnet", json.loads(showsubnetsresponse.content)["subnet"]["name"])
        print(" ")

        print('->>>>>>> testNeutronShowNonExistingSubnet->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets/non-existing-id123"
        showsubnetsresponse = requests.get(url, headers=headers)
        self.assertEqual(showsubnetsresponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronCreateSubnetInNonExistingNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        createnosubnetdata = '{"subnet": {"name": "new_subnet", "network_id": "non-existing-networkid123","ip_version": 4,"cidr": "10.0.0.1/24"} }'
        createsubnetresponse = requests.post(url, data=createnosubnetdata, headers=headers)
        self.assertEqual(createsubnetresponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronCreateSubnetWithWrongCIDR ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        createsubnetdatawithwrongcidr = '{"subnet": {"name": "new_subnet_with_wrong_cidr", "network_id": "%s","ip_version": 4,"cidr": "10.0.0.124"} }' % (
        json.loads(createnetworkresponse.content)["network"]["id"])
        createsubnetwrongcirdresponse = requests.post(url, data=createsubnetdatawithwrongcidr, headers=headers)
        self.assertEqual(createsubnetwrongcirdresponse.status_code, 400)
        print(" ")

        print('->>>>>>> testNeutronCreateSubnetWithoutCIDR ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        createsubnetdatawithoutcidr = '{"subnet": {"name": "new_subnet", "network_id": "%s","ip_version": 4, "allocation_pools":"change_me", "gateway_ip":"10.0.0.1", "id":"new_id123", "enable_dhcp":true} }' % (
        json.loads(createnetworkresponse.content)["network"]["id"])
        createsubnetwithoutcirdresponse = requests.post(url, data=createsubnetdatawithoutcidr, headers=headers)
        self.assertEqual(createsubnetwithoutcirdresponse.status_code, 400)
        print(" ")

        print('->>>>>>> testNeutronCreateSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        createsubnetdata = '{"subnet": {"name": "new_subnet", "network_id": "%s","ip_version": 4,"cidr": "10.0.0.1/24"} }' % (json.loads(createnetworkresponse.content)["network"]["id"])
        createsubnetresponse = requests.post(url, data=createsubnetdata, headers=headers)
        self.assertEqual(createsubnetresponse.status_code, 201)
        self.assertEqual(json.loads(createsubnetresponse.content)["subnet"]["name"], "new_subnet")
        print(" ")

        print('->>>>>>> testNeutronCreateSecondSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets"
        createsubnetdata = '{"subnet": {"name": "new_subnet", "network_id": "%s","ip_version": 4,"cidr": "10.0.0.1/24"} }' % (json.loads(createnetworkresponse.content)["network"]["id"])
        createsubnetfailureresponse = requests.post(url, data=createsubnetdata, headers=headers)
        self.assertEqual(createsubnetfailureresponse.status_code, 409)
        print(" ")

        print('->>>>>>> testNeutronUpdateSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets/%s" % (json.loads(createsubnetresponse.content)["subnet"]["id"])
        updatesubnetdata = '{"subnet": {"name": "new_subnet_new_name", "network_id":"some_id", "tenant_id":"new_tenant_id", "allocation_pools":"change_me", "gateway_ip":"192.168.1.120", "ip_version":4, "cidr":"10.0.0.1/24", "id":"some_new_id", "enable_dhcp":true} }'
        updatesubnetresponse = requests.put(url, data=updatesubnetdata, headers=headers)
        self.assertEqual(updatesubnetresponse.status_code, 200)
        self.assertEqual(json.loads(updatesubnetresponse.content)["subnet"]["name"], "new_subnet_new_name")
        print(" ")

        print('->>>>>>> testNeutronUpdateNonExistingSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/subnets/non-existing-subnet-12345"
        updatenonexistingsubnetdata = '{"subnet": {"name": "new_subnet_new_name"} }'
        updatenonexistingsubnetresponse = requests.put(url, data=updatenonexistingsubnetdata, headers=headers)
        self.assertEqual(updatenonexistingsubnetresponse.status_code, 404)
        print(" ")



        print('->>>>>>> testNeutronListPorts ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports"
        listportsesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsesponse.status_code, 200)
        self.assertEqual(json.loads(listportsesponse.content)["ports"][0]["status"], "ACTIVE")
        listPortsName = json.loads(listportsesponse.content)["ports"][0]["name"]
        listPortsId1 = json.loads(listportsesponse.content)["ports"][0]["id"]
        listPortsId2 = json.loads(listportsesponse.content)["ports"][1]["id"]
        print(" ")

        print('->>>>>>> testNeutronListPortsByName ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports?name=" + listPortsName
        listportsbynameesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbynameesponse.status_code, 200)
        self.assertEqual(json.loads(listportsbynameesponse.content)["ports"][0]["name"], listPortsName)
        print(" ")

        print('->>>>>>> testNeutronListPortsById ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports?id=" + listPortsId1
        listportsbyidesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbyidesponse.status_code, 200)
        self.assertEqual(json.loads(listportsbyidesponse.content)["ports"][0]["id"], listPortsId1)
        print(" ")

        print('->>>>>>> testNeutronListPortsByMultipleIds ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports?id=" + listPortsId1 +"&id="+listPortsId2
        listportsbymultipleidsesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbymultipleidsesponse.status_code, 200)
        self.assertEqual(json.loads(listportsbymultipleidsesponse.content)["ports"][0]["id"], listPortsId1)
        print(" ")

        print('->>>>>>> testNeutronListNonExistingPorts ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports?id=non-existing-port-id"
        listportsbynonexistingidsesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbynonexistingidsesponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronShowPort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports/%s" % (json.loads(listportsesponse.content)["ports"][0]["id"])
        showportresponse = requests.get(url, headers=headers)
        self.assertEqual(showportresponse.status_code, 200)
        self.assertEqual(json.loads(showportresponse.content)["port"]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> testNeutronShowNonexistingPort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports/non-existing-portid123"
        shownonexistingportresponse = requests.get(url, headers=headers)
        self.assertEqual(shownonexistingportresponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronCreatePortInNonExistingNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports"
        createnonexistingportdata = '{"port": {"name": "new_port", "network_id": "non-existing-id"} }'
        createnonexistingnetworkportresponse = requests.post(url, data=createnonexistingportdata, headers=headers)
        self.assertEqual(createnonexistingnetworkportresponse.status_code, 404)
        print(" ")

        #TODO seems as something wents wrong if i set the id in the data field: "id":"new_id1234"
        # then other parts do not find the port by the id...
        print('->>>>>>> testNeutronCreatePort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports"
        createportdata = '{"port": {"name": "new_port", "network_id": "%s", "admin_state_up":true, "device_id":"device_id123", "device_owner":"device_owner123", "fixed_ips":"change_me","mac_address":"12:34:56:78:90", "status":"change_me", "tenant_id":"tenant_id123"} }' % (json.loads(createnetworkresponse.content)["network"]["id"])
        createportresponse = requests.post(url, data=createportdata, headers=headers)
        self.assertEqual(createportresponse.status_code, 201)
        print (createportresponse.content)
        self.assertEqual(json.loads(createportresponse.content)["port"]["name"], "new_port")
        print(" ")

        print('->>>>>>> testNeutronCreatePortWithExistingName ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports"
        createportwithexistingnamedata = '{"port": {"name": "new_port", "network_id": "%s"} }' % (json.loads(createnetworkresponse.content)["network"]["id"])
        createportwithexistingnameresponse = requests.post(url, data=createportwithexistingnamedata, headers=headers)
        self.assertEqual(createportwithexistingnameresponse.status_code, 500)
        print(" ")

        print('->>>>>>> testNeutronCreatePortWithoutName ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports"
        createportdatawithoutname = '{"port": {"network_id": "%s"} }' % (json.loads(createnetworkresponse.content)["network"]["id"])
        createportwithoutnameresponse = requests.post(url, data=createportdatawithoutname, headers=headers)
        self.assertEqual(createportwithoutnameresponse.status_code, 201)
        self.assertIn("port:cp", json.loads(createportwithoutnameresponse.content)["port"]["name"])
        print(" ")

        print('->>>>>>> testNeutronUpdatePort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print json.loads(createportresponse.content)["port"]["name"]
        url = "http://0.0.0.0:9696/v2.0/ports/%s" % (json.loads(createportresponse.content)["port"]["name"])
        updateportdata = '{"port": {"name": "new_port_new_name", "admin_state_up":true, "device_id":"device_id123", "device_owner":"device_owner123", "fixed_ips":"change_me","mac_address":"12:34:56:78:90", "status":"change_me", "tenant_id":"tenant_id123", "network_id":"network_id123"} }'
        updateportresponse = requests.put(url, data=updateportdata, headers=headers)
        self.assertEqual(updateportresponse.status_code, 200)
        self.assertEqual(json.loads(updateportresponse.content)["port"]["name"], "new_port_new_name")
        print(" ")

        print('->>>>>>> testNeutronUpdateNonExistingPort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:9696/v2.0/ports/non-existing-port-ip"
        updatenonexistingportdata = '{"port": {"name": "new_port_new_name"} }'
        updatenonexistingportresponse = requests.put(url, data=updatenonexistingportdata, headers=headers)
        self.assertEqual(updatenonexistingportresponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronDeletePort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        righturl = "http://0.0.0.0:9696/v2.0/ports/%s" % (json.loads(createportresponse.content)["port"]["id"])
        deleterightportresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deleterightportresponse.status_code, 204)
        print(" ")


        print('->>>>>>> testNeutronDeleteNonExistingPort ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:9696/v2.0/ports/unknownid"
        deletewrongportresponse = requests.delete(wrongurl, headers=headers)
        self.assertEqual(deletewrongportresponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNeutronDeleteSubnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:9696/v2.0/subnets/unknownid"
        righturl = "http://0.0.0.0:9696/v2.0/subnets/%s" % (json.loads(updatesubnetresponse.content)["subnet"]["id"])
        deletewrongsubnetresponse = requests.delete(wrongurl, headers=headers)
        deleterightsubnetresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deletewrongsubnetresponse.status_code, 404)
        self.assertEqual(deleterightsubnetresponse.status_code, 204)
        print(" ")

        print('->>>>>>> testNeutronDeleteNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        righturl = "http://0.0.0.0:9696/v2.0/networks/%s" % (json.loads(createnetworkresponse.content)["network"]["id"])
        deleterightnetworkresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deleterightnetworkresponse.status_code, 204)
        print(" ")

        print('->>>>>>> testNeutronDeleteNonExistingNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:9696/v2.0/networks/unknownid"
        deletewrongnetworkresponse = requests.delete(wrongurl, headers=headers)
        self.assertEqual(deletewrongnetworkresponse.status_code, 404)
        print(" ")

    def testKeystomeDummy(self):
        headers = {'Content-type': 'application/json'}
        test_heatapi_keystone_get_token = open(os.path.join(os.path.dirname(__file__), "test_heatapi_keystone_get_token.json")).read()
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
        test_heatapi_template_create_stack = open(os.path.join(os.path.dirname(__file__), "test_heatapi_template_create_stack.json")).read()
        test_heatapi_template_update_stack = open(os.path.join(os.path.dirname(__file__), "test_heatapi_template_update_stack.json")).read()
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


if __name__ == '__main__':
    unittest.main()
