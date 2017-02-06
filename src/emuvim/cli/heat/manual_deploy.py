#! /usr/bin/env python
import requests
import logging
import json
import time
import argparse
neutron_baseport = 9697
nova_baseport = 8775
ip_or_hostname = "http://localhost"
neutron_baseurl = "/v2.0"
nova_baseurl = "/v2.1/fc394f2ab2df4114bde39905f800dc57"

logging.basicConfig(level=logging.DEBUG)

def run_request(resource, data=None, dc=0, req="GET", nova=False, neutron=False, chain=False, headers=None):
    if not nova and not neutron and not chain:
        return False

    resp = None
    url = None
    if nova:
        url = "%s:%d%s%s" % (ip_or_hostname, (nova_baseport + dc), nova_baseurl, resource)
    if neutron:
        url = "%s:%d%s%s" % (ip_or_hostname, (neutron_baseport + dc), neutron_baseurl, resource)
    if chain:
        url = "%s:%d%s%s" % (ip_or_hostname, 4000, "/v1", resource)

    if not headers:
        headers = {'Content-type': 'application/json'}

    if req.upper() == "GET":
        logging.debug("GET %s" % url)
        resp = requests.get(url, data=data, headers=headers)
    if req.upper() == "POST":
        logging.debug("POST %s DATA: %s" % (url, data))
        resp = requests.post(url, data=data, headers=headers)
    if req.upper() == "PUT":
        logging.debug("PUT %s DATA: %s" % (url, data))
        resp = requests.put(url, data=data, headers=headers)
    if req.upper() == "DELETE":
        logging.debug("DELETE %s DATA: %s" % (url, data))
        resp = requests.delete(url, data=data, headers=headers)

    if resp is not None:
        logging.debug("RESPONSE: %s" % resp.content)
    else:
        logging.debug("EMPTY RESPONSE")
    return resp


def create_server(name, flavor, image, portid, datacenter=0):
    logging.debug("Creating server %s with portid %s" % (name, portid))

    # we need the flavor id
    resp = run_request("/flavors", nova=True, dc=datacenter)
    flavors = json.loads(resp.content)['flavors']
    flavorid = 0
    for fl in flavors:
        if str(fl['name']) == flavor:
            flavorid = fl['id']
            break

    # and the image id
    resp = run_request("/images", nova=True, dc=datacenter)
    images = json.loads(resp.content)['images']
    imageid = 0
    for img in images:
        if str(img['name']) == image:
            imageid = img['id']
            break

    if imageid == 0 or flavorid == 0:
        logging.warning("Could not find image or flavor id. For image %s and flavor %s." % (image, flavor))
        return False

    if isinstance(portid, list):
        port_list = list()
        for port in portid:
            port_list.append({"port": port})

        data = '{"server": {' \
               '"name": "%s",' \
               '"imageRef": "%s",' \
               '"flavorRef": "%s",' \
               '"max_count": "1",' \
               '"min_count": "1",' \
               '"networks": %s}}' % (name, imageid, flavorid, json.dumps(port_list))
    else:
        data = '{"server": {' \
               '"name": "%s",' \
               '"imageRef": "%s",' \
               '"flavorRef": "%s",' \
               '"max_count": "1",' \
               '"min_count": "1",' \
               '"networks": [{"port": "%s"}]}}' % (name, imageid, flavorid, portid)
    resp = run_request("/servers",data=data, nova=True, req="POST", dc=datacenter)
    return json.loads(resp.content)


def create_network_and_subnet(name, cidr=None, datacenter=0):
    logging.debug("Creating network %s" % (name))
    networkid = 0
    data = '{"network": {"name": "%s","admin_state_up": true}}' % name
    resp = run_request("/networks", data=data, neutron=True, req="POST", dc=datacenter)
    if resp.status_code == 400:
        resp = run_request("/networks", neutron=True, dc=datacenter)
        for net in json.loads(resp.content)["networks"]:
            if net["name"] == name:
                networkid = net["id"]

    else:
        networkid = json.loads(resp.content)["network"]["id"]

    data = '{"subnet": {"name": "%s-sub","network_id": "%s","ip_version": "4","cidr": "%s"}}' % (name, networkid, cidr)
    resp = run_request("/subnets", data=data, neutron=True, req="POST", dc=datacenter)

    return networkid

def create_port(network_id, datacenter, name = None):
    if name is not None:
        data = '{"port": {"network_id": "%s", "name": "%s"} }' % (network_id, name)
    else:
        data = '{"port": {"network_id": "%s"} }' % (network_id)
    resp = run_request("/ports", data=data, neutron=True, req="POST", dc=datacenter)
    return json.loads(resp.content)["port"]["id"]

def add_floatingip_to_server(server, datacenter):
    resp = assign_floating_ip_to_server(server, datacenter)
    return resp

def create_floating_ip(datacenter):
    data = '{"floatingip":{"floating_network_id":"floating-network"}}'
    resp = run_request("/floatingips", data=data, neutron=True, req="POST", dc=datacenter)
    return json.loads(resp.content)["floatingip"]["port_id"]

def assign_floating_ip_to_server(server_id, datacenter):
    data = '{"interfaceAttachment":{"net_id":"floating-network"}}'
    resp = run_request("/servers/%s/os-interface" % str(server_id), data=data, nova=True, req="POST", dc=datacenter)
    return json.loads(resp.content)

def assign_intf_to_server(server_id, port_id, datacenter):
    data = '{"interfaceAttachment":{"port_id":"%s"}}' % port_id
    resp = run_request("/servers/%s/os-interface" % str(server_id), data=data, nova=True, req="POST", dc=datacenter)
    return json.loads(resp.content)

def add_loadbalancer(server, intface, lb_data):
    data = json.dumps(lb_data)
    resp = run_request("/lb/%s/%s" % (str(server), str(intface)), data=data, chain=True, req="POST")
    return resp

def set_chain(src_vnf, src_intf, dst_vnf, dst_intf, data=None):
    if data is None:
        data = {}
    data = json.dumps(data)
    resp = run_request("/chain/%s/%s/%s/%s" % (src_vnf, src_intf, dst_vnf, dst_intf), data=data, chain=True, req="POST")

def delete_chain(src_vnf, src_intf, dst_vnf, dst_intf, data=None):
    resp = run_request("/chain/%s/%s/%s/%s" % (src_vnf, src_intf, dst_vnf, dst_intf), data=data, chain=True, req="DELETE")

def create_network_and_port(port_name=None, datacenter=0, net_name=None, cidr=None):
    netid = create_network_and_subnet(net_name, cidr, datacenter=datacenter)
    portid = create_port(netid, datacenter=datacenter, name=port_name)
    return netid, portid

def sample_topo():
    for dc in range(4):
        net = create_network_and_subnet("test%s" % dc, "192.168.%d.0/24" % (dc+2), datacenter=dc)

        for x in range(2):
            port = create_port(net, datacenter=dc)
            server = create_server("serv%s" %x, "m1.tiny", "ubuntu:trusty", port, datacenter=dc)
            add_floatingip_to_server(server["server"]["id"], datacenter=dc)

    lb_data = {"dst_vnf_interfaces": {"dc1_man_serv1": "port-man-2","dc2_man_serv0": "port-man-3",
                                      "dc2_man_serv1": "port-man-4"}}
    add_loadbalancer("dc1_man_serv0", "port-cp0-man", lb_data)


def chain_topo_test():
    for dc in range(4):
        net = create_network_and_subnet("test%s" % dc, "192.168.%d.0/24" % (dc+2), datacenter=dc)

        for x in range(1):
            port = create_port(net, datacenter=dc)
            server = create_server("serv%s" %x, "m1.tiny", "ubuntu:trusty", port, datacenter=dc)

    #data = {"path": ["dc1.s1", "s1", "dc4.s1"]}
    #data = None
    set_chain("dc1_man_serv0","port-man-0","dc4_man_serv0","port-man-3",data)
    data = {"layer2": True}
    set_chain("dc1_man_serv0", "port-man-0", "dc2_man_serv0", "port-man-1", data)

def lb_webservice_topo():
    # floating entrypoint
    net = create_network_and_subnet("net1", "192.168.2.0/24", datacenter=0)
    port = create_port(net, datacenter=0)

    # web and db in datacenter 2
    dc = 1
    netid, portid = create_network_and_port(net_name="net3", cidr="192.168.3.0/24", datacenter=dc)
    netid2, portid2 = create_network_and_port(net_name="net4", cidr="192.168.4.0/24",
                                              datacenter=dc, port_name="port-out")
    db_in_port = create_port(netid2, datacenter=dc)
    server = create_server("db", "m1.tiny", "xschlef/database:latest", db_in_port, datacenter=dc)
    server = create_server("web", "m1.tiny", "xschlef/webserver:latest",[portid, portid2], datacenter=dc)

    # web in datacenter 3
    dc = 2
    netid, portid = create_network_and_port(net_name="net3", cidr="192.168.5.0/24", datacenter=dc)
    netid2, portid2 = create_network_and_port(net_name="net4", cidr="192.168.6.0/24",
                                              datacenter=dc, port_name="port-out")
    server = create_server("web", "m1.tiny", "xschlef/webserver:latest", [portid, portid2], datacenter=dc)

    # web in datacenter 4
    dc = 3
    netid, portid = create_network_and_port(net_name="net3", cidr="192.168.7.0/24", datacenter=dc)
    netid2, portid2 = create_network_and_port(net_name="net4", cidr="192.168.8.0/24",
                                              datacenter=dc, port_name="port-out")
    server = create_server("web", "m1.tiny", "xschlef/webserver:latest", [portid, portid2], datacenter=dc)


    lb_data = {"dst_vnf_interfaces": {"dc2_man_web": "port-man-1", "dc3_man_web": "port-man-3","dc4_man_web": "port-man-4"}}

    add_loadbalancer("floating","dc1", lb_data)

    set_chain("dc2_man_web", "port-out-0", "dc2_man_db", "port-man-2")
    set_chain("dc3_man_web", "port-out-1", "dc2_man_db", "port-man-2")
    set_chain("dc4_man_web", "port-out-2", "dc2_man_db", "port-man-2")


if __name__ == "__main__":
    #sample_topo()
    lb_webservice_topo()
    #chain_topo_test()

