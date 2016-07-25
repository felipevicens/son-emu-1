from __future__ import print_function  # TODO remove when print is no longer needed fore debugging
import ruamel.yaml
import sys


class YAMLReader:
    def __init__(self):
        self.description = None
        self.parameter_groups = None
        self.parameters = None
        self.resources = None
        self.outputs = None

    def parse_input(self, input_string):
        code = ruamel.yaml.load(input_string, ruamel.yaml.RoundTripLoader)

        if not (str(code[
                        'heat_template_version']) == '2015-04-30'):  # TODO: change to versions equal or later than this date (to check that it is a HOT template)
            print('Unsupported template version: ' + code['heat_template_version'], file=sys.stderr)
            return

        try:
            self.description = code['description']
        except Exception as e:
            self.description = None
            print('No ' + e.message + ' found.')

        try:
            self.parameter_groups = code['parameter_groups']
        except Exception as e:
            self.parameter_groups = None
            print('No ' + e.message + ' found.')

        try:
            self.parameters = code['parameters']
        except Exception as e:
            self.parameters = None
            print('No ' + e.message + ' found.')

        try:
            self.resources = code['resources']
        except Exception as e:
            self.resources = None
            print('No ' + e.message + ' found.')

        try:
            self.outputs = code['outputs']
        except Exception as e:
            self.outputs = None
            print('No ' + e.message + ' found.')

        print(ruamel.yaml.dump(code['resources'], Dumper=ruamel.yaml.RoundTripDumper), end='')

        if self.resources is not None:
            self.get_datacenters(code['resources'])

    def get_datacenters(self, datacenter_yaml_part):
        try:
            x = datacenter_yaml_part[
                'datacenters']  # TODO: change to the right position within the HOT template (dont know it right now)
        except Exception as e:
            pass


if __name__ == '__main__':
    inputFile = open('yamlTest1', 'r')
    inp = inputFile.read()
    x = YAMLReader()
    x.parse_input(inp)
