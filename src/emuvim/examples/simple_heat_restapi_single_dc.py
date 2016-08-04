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
import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint

from emuvim.api.zerorpc.compute import ZeroRpcApiEndpoint
from emuvim.api.heat.resources import *
from emuvim.api.heat.heat_api_endpoint import HeatApiEndpoint
from emuvim.api.zerorpc.network import ZeroRpcApiEndpointDCNetwork

logging.basicConfig(level=logging.INFO)


def create_topology1():
    net = DCNetwork(monitor=True, enable_learning=True)
    dc1 = net.addDatacenter("datacenter1")

    heatapi1 = HeatApiEndpoint("0.0.0.0", 5001)

    # connect data center to this endpoint
    heatapi1.connect_datacenter(dc1)

    # heatapirun API endpoint server (in another thread, don't block)
    heatapi1.start()

    # connect data center to this endpoint
    heatapi1.connect_datacenter(dc1)

    heatapi1.connect_dc_network(net)

    net.start()
    net.CLI()
    # when the user types exit in the CLI, we stop the emulator
    net.stop()


def main():
    setLogLevel('info')  # set Mininet loglevel
    create_topology1()


if __name__ == '__main__':
    main()
