#!/bin/bash
#curl -X POST -d '{"dpid":"1001","type":"ALL","group_id":"1","buckets":[{"actions":[{"type":"OUTPUT","port":"5"}]},{"actions":[{"type":"OUTPUT","port":"4"}]},{"actions":[{"type":"OUTPUT","port":"3"}]}]}' http://localhost:8080/stats/groupentry/add
#curl -X POST -d '{"dpid": 1001,"match":{"in_port": 2},"actions":[{"type":"GROUP","group_id": 1}]}' http://localhost:8080/stats/flowentry/add

#curl -X POST -d "{'buckets': [{'actions': [{'type': 'OUTPUT', 'port': 3}]}, {'actions': [{'type': 'OUTPUT', 'port': 5}]}, {'actions': [{'type': 'OUTPUT', 'port': 4}]}], 'priority': 0, 'cookie': 1, 'dpid': 1001, 'group_id': 1, 'type': 'select'}" -H "Content-Type: application/json" http://localhost:8080/stats/groupentry/add
#curl -X GET http://localhost:8080/stats/flow/1001

# ovs-ofctl -O OpenFlow13 add-group dc1.s1 group_id=1,type=all,bucket=output:3,bucket=output:4,bucket=output:5

curl -X POST -d '{"dst_vnf_interfaces": {"dc1_man_serv1": "port-cp1-man","dc1_man_serv2": "port-cp2-man","dc1_man_serv3": "port-cp3-man"}}' -H "Content-Type: application/json" http://localhost:4000/v1/lb/dc1_man_serv0/port-cp0-man
