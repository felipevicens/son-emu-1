ovs-ofctl -OOpenFlow13 add-flow dc1.s1 "ip,table=0,in_port=2,actions=load:0x1->NXM_NX_REG0[],multipath(symmetric_l4, 1024, modulo_n, 3, 0, NXM_NX_REG1[0..12]),resubmit(,10)"

#group_id=1,type=select,bucket=actions=push_vlan:0x8100,set_field:4096->vlan_vid,set_field:22:cb:c7:b3:8a:91->eth_dst,set_field:192.168.2.3->ip_dst,output:1,bucket=actions=push_vlan:0x8100,set_field:4098->vlan_vid,set_field:ae:2f:a4:a2:0b:04->eth_dst,set_field:192.168.2.3->ip_dst,output:1,bucket=actions=push_vlan:0x8100,set_field:4100->vlan_vid,set_field:4a:18:cf:3e:6c:76->eth_dst,set_field:192.168.2.3->ip_dst,output:1
ovs-ofctl -OOpenFlow13 add-flow dc1.s1 "ip,table=10,reg1=0,actions=push_vlan:0x8100,set_field:4096->vlan_vid,set_field:ae:2f:a4:a2:0b:04->eth_dst,set_field:192.168.2.3->ip_dst,output:1"
ovs-ofctl -OOpenFlow13 add-flow dc1.s1 "ip,table=10,reg1=1,actions=push_vlan:0x8100,set_field:4098->vlan_vid,set_field:22:cb:c7:b3:8a:91->eth_dst,set_field:192.168.2.3->ip_dst,output:1"
ovs-ofctl -OOpenFlow13 add-flow dc1.s1 "ip,table=10,reg1=2,actions=push_vlan:0x8100,set_field:4100->vlan_vid,set_field:4a:18:cf:3e:6c:76->eth_dst,set_field:192.168.2.3->ip_dst,output:1"

ovs-ofctl -OOpenFlow13 add-flow dc1.s1 cookie=0x4,in_port=1,dl_vlan=3,actions=pop_vlan,output:2
ovs-ofctl -OOpenFlow13 add-flow dc1.s1 cookie=0x6,in_port=1,dl_vlan=5,actions=pop_vlan,output:2
ovs-ofctl -OOpenFlow13 add-flow dc1.s1 cookie=0x2,in_port=1,dl_vlan=1,actions=pop_vlan,output:2
ovs-ofctl add-flow "arp,arp_tpa=192.168.2.3,actions=load:0x2->NXM_OF_ARP_OP[],move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[],set_field:01:23:45:67:89:ab->eth_src,move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[],move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[],load:0x123456789ab->NXM_NX_ARP_SHA[],load:0xc0a80203->NXM_OF_ARP_SPA[],IN_PORT"
