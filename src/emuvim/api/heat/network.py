from ryu.services.protocols.vrrp import router

net = None
port_list = []
subnet_list = []
net_list = []
floating_ip_list = []
router_interface_list = []
router_list = []

def add_port(name, network):
    port = Port(name, network)
    port_list.__add__(port)

def add_subnet(cidr, gateway_ip, name, network):
    subnet = Subnet(cidr, gateway_ip, name, network)
    subnet_list.__add__(subnet)

def add_net(name):
    net = Net(name)
    net_list.__add__(net)

def add_floating_ip(network_id, port_id):
    floating_ip = FloatingIP(network_id, port_id)
    floating_ip_list.__add__(floating_ip)

def add_router_interface(router, subnet):
    router_interface = RouterInterface(router, subnet) #TODO use existing router/subnet ???
    router_interface_list.__add__(router_interface)

def add_router(name):
    router = Router(name)
    router_list.__add__(router)



class Port:
    def __init__(self, name, network):
        self.name = name
        self.network = network


class Subnet:
    def __init__(self, cidr, gateway_ip, name, network):
        self.cidr = cidr
        self.gateway_ip = gateway_ip
        self.name = name
        self.network = network


class Net:
    def __init__(self, name):
        self.name = name


class FloatingIP:
    def __init__(self, network_id, port_id):
        self.network_id = network_id
        self.port_id = port_id


class RouterInterface:
    def __init__(self, router, subnet):
        self.router = router
        self.subnet = subnet


class Router:
    def __init__(self, name):
        self.name = name