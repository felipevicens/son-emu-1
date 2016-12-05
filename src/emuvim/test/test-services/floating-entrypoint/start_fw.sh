#!/bin/bash
echo "FloatingIP entrypoint container started"

fl_intf=""
while [ -z $fl_intf ]
do
for i in `ls /sys/class/net`
do
   if [[ $i =~ port.*fl ]]
   then
      fl_intf=$i
   else
      if [[ $i =~ port.* ]]
      then
          int_intf=$i
          offset=`ip a s $i | grep -oP 'inet \K\S+' |cut -d/ -f1 | cut -d. -f4`
          ((offset+=1))
          ip1=`ip a s $i | grep -oP 'inet \K\S+' |cut -d/ -f1 | cut -d. -f1`
          ip2=`ip a s $i | grep -oP 'inet \K\S+' |cut -d/ -f1 | cut -d. -f2`
          ip3=`ip a s $i | grep -oP 'inet \K\S+' |cut -d/ -f1 | cut -d. -f3`
          new_ip="$ip1.$ip2.$ip3.$offset"
      fi
   fi
done
sleep 1
done

echo "adding iptables rules"
iptables -t nat -A POSTROUTING -o $int_intf -j MASQUERADE
iptables -t nat -A POSTROUTING -o $fl_intf -j MASQUERADE
iptables -t nat -A PREROUTING -i $fl_intf -j DNAT --to $new_ip

