#! /usr/bin/env python
import requests
import logging
import json
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

def create_port(network_id, datacenter):
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

def add_loadbalancer(server, intface, lb_data):
    # ''
    data = json.dumps(lb_data)
    resp = run_request("/lb/%s/%s" % (str(server), str(intface)), data=data, chain=True, req="POST")
    return resp


def sample_topo():
    for dc in xrange(4):
        net = create_network_and_subnet("test%s" % dc, "192.168.%d.0/24" % (dc+2), datacenter=dc)

        for x in xrange(2):
            port = create_port(net, datacenter=dc)
            server = create_server("serv%s" %x, "m1.tiny", "ubuntu:trusty", port, datacenter=dc)
            add_floatingip_to_server(server["server"]["id"], datacenter=dc)

    lb_data = {"dst_vnf_interfaces": {"dc1_man_serv1": "port-cp2-man","dc2_man_serv0": "port-cp0-man",
                                      "dc2_man_serv1": "port-cp2-man"}}
    add_loadbalancer("dc1_man_serv0", "port-cp0-man", lb_data)


if __name__ == "__main__":
    sample_topo()

