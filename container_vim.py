#!/usr/bin/python2
"""
Copyright (c) 2017 SONATA-NFV, Paderborn Univserity
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
TODOs
- connect OVS of this PoP to an external controller (RemoteController)

"""
import logging
import argparse
import mininet.log
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from mininet.node import Controller

# set default log levels
logging.basicConfig()  
mininet.log.setLogLevel('info')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("docker").setLevel(logging.WARNING)


class SonataContainerVim(object):

    def __init__(self, name, listen_to="0.0.0.0", port=5001):
        # parameters
        self.name = name
        self.listen_to = listen_to
        self.port = int(port)
        # members
        self.net = None
        
    def _setup_pop(self):
        # setup a single emulator datacenter (a single OVSSwitch)
        self.net = DCNetwork(controller=Controller)
        dc1 = self.net.addDatacenter(self.name)
        # start rest API
        api = RestApiEndpoint(self.listen_to, self.port)
        api.connectDCNetwork(self.net)
        api.connectDatacenter(dc1)
        api.start()

    def _welcome_screen(self):
        logging.info("*" * 36)
        logging.info("**")
        logging.info("**\tSONATA Container VIM")
        logging.info("**")
        logging.info("** Listening to {0}:{1}".format(self.listen_to, self.port))
        logging.info("**")
        logging.info("** VIM: '{0}' ...ready.".format(self.name))
        logging.info("*" * 36)

    def start_pop(self):
        # setup a single datacenter inside the emulator
        self._setup_pop()
        # start the network (switch, REST interface etc.)
        self.net.start()
        self._welcome_screen()
        # open interactive CLI until 'exit' was typed
        self.net.CLI()
        # tear down network
        self.net.stop()


def parse_args():
    parser = argparse.ArgumentParser(
        description="SONATA Container VIM (based on son-emu)")

    parser.add_argument(
        "-v",
        "--verbose",
        help="Enable more verbose outputs.",
        required=False,
        default=False,
        action="store_true",
        dest="verbose")

    parser.add_argument(
        "-n",
        help="Name of this container VIM PoP. Default: 'cvim1'.",
        required=False,
        default="cvim1",
        dest="name")

    parser.add_argument(
        "-l",
        help="REST interface: IP to listen. Default: '0.0.0.0'.",
        required=False,
        default="0.0.0.0",
        dest="listen")

    parser.add_argument(
        "-p",
        help="REST interface: Port to listen. Default: '5001'.",
        required=False,
        default="5001",
        dest="port")

    return parser.parse_args()

        
def main():
    # parse inputs
    args = parse_args()
    # enable verbose logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        logging.getLogger("werkzeug").setLevel(logging.DEBUG)
        logging.getLogger("docker").setLevel(logging.DEBUG)
    # start container vim
    scv = SonataContainerVim(args.name, listen_to=args.listen, port=args.port)
    scv.start_pop()

if __name__ == '__main__':
    main()
