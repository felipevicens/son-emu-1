from __future__ import print_function  # TODO remove when print is no longer needed for debugging
import yaml
import sys
import compute
import network


class YAMLReader:
    def __init__(self):
        self.description = None
        self.parameter_groups = None
        self.parameters = None
        self.resources = None
        self.outputs = None

    def parse_input(self, input_string):
        yaml_file = yaml.load(input_string)

        if not (str(yaml_file['heat_template_version']) == '2015-04-30'):  # TODO: change to versions equal or later then this date (to check that it is a HOT template)
            print('Unsupported template version: ' + yaml_file['heat_template_version'], file=sys.stderr)
            return

        try:
            self.description = yaml_file['description']
        except Exception as e:
            self.description = None
            print('No ' + e.message + ' found.')

        try:
            self.parameter_groups = yaml_file['parameter_groups']
        except Exception as e:
            self.parameter_groups = None
            print('No ' + e.message + ' found.')

        try:
            self.parameters = yaml_file['parameters']
        except Exception as e:
            self.parameters = None
            print('No ' + e.message + ' found.')

        try:
            self.resources = yaml_file['resources']
        except Exception as e:
            self.resources = None
            print('No ' + e.message + ' found.')

        try:
            self.outputs = yaml_file['outputs']
        except Exception as e:
            self.outputs = None
            print('No ' + e.message + ' found.')

        #print(yaml.dump(self.resources, default_flow_style=False), end='')


        for resource in self.resources:
            try:
                self.handle_recource(self.resources[resource])
            except Exception as e:
                print('Some error occured: ' + e.message)



        if self.resources is not None:
            self.get_datacenters(yaml_file['resources'])

    def get_datacenters(self, datacenter_yaml_part):
        try:
            x = datacenter_yaml_part['datacenters']  # TODO: change to the right position within the HOT template (dont know it right now)
        except Exception as e:
            pass


    def handle_recource(self, resource): #TODO are all resource references complete?
        if "Net" in resource['type']:
            #print('Net')
            network.add_net(resource['properties']['name'])
            return

        if 'Subnet' in resource['type']:
            #print('Subnet')
            cidr = resource['properties']['cidr']
            gateway_ip = resource['properties']['gateway_ip']
            name = resource['properties']['name']
            network_dict = resource['properties']['network']
            network.add_subnet(cidr, gateway_ip, name, network_dict)
            return

        if 'Port' in resource['type']:
            #print('Port')
            network.add_port(resource['properties']['name'], resource['properties']['network'])
            return

        if 'Server' in resource['type']:
            print('Server')
            compute_name = resource['properties']['name']
            nw_list = resource['properties']['networks']
            image = resource['properties']['image']
            command = 'dockerCommand' #TODO findout what the command does!!!!!!
            compute.add_server(compute_name, nw_list, image, command)
            return

        if 'RouterInterface' in resource['type']:
            #print('RouterInterface')
            network.add_router_interface(resource['properties']['router']['get_resource'], resource['properties']['subnet']['get_resource'])
            return

        if 'FloatingIP' in resource['type']:
            #print('FloatingIP')
            network.add_floating_ip(resource['properties']['floating_network_id'], resource['properties']['port_id']['get_resource'])
            return

        if 'Router' in resource['type'] and 'RouterInterface' not in resource['type']: #TODO find a better way to isolate Router from RouterInterface
            #print('Router')
            network.add_router(resource['properties']['name'])
            return




if __name__ == '__main__':
    inputFile = open('yamlTest2', 'r')
    inp = inputFile.read()
    inputFile.close()
    x = YAMLReader()
    x.parse_input(inp)

