
dcs = {}

server_list = []

def add_server(compute_name, network, image, command):
    server = Heat_Server(compute_name, network, image, command)
    server_list.__add__(server)



class Heat_Server:

    def __init__(self, compute_name, network, image, command):
        self.compute_name = compute_name
        self.network = network
        self.image = image
        self.command = command
