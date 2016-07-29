
import yaml

dcs = {}

server_list = []

def add_server(compute_name, network, image, command):
    server = Heat_Server(compute_name, network, image, command)
    server_list.append(server)

def parse_server_network(network):
    '''
    TODO how to create networks like
     [{"id":x, "ip":"x.x.x.x/x"}, ...]
    from our example?
    '''
    newNetwork = {}
    iterator = 0
    for port in network: #TODO change the IPs ! the example does not contain real IPs
        newNetwork.update({'id': iterator, 'ip': port['port']['get_resource']}) #it rewrites the id and ip each time! thus we only get one entry but we want to have all 3
        iterator += 1
    #print(yaml.dump(newNetwork, default_flow_style=False))
    return newNetwork

class Heat_Server:

    def __init__(self, compute_name, network, image, command):
        self.compute_name = compute_name
        self.network = network
        self.image = image
        self.command = command

    def start_compute(self, dc_label):
        c = dcs.get(dc_label).startCompute(self.compute_name, self.image, self.command, self.network)
        return c.getStatus()