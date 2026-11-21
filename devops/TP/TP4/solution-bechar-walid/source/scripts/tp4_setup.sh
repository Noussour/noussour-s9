#!/bin/bash
# Recreates the TP4 student resources so Horizon screenshots can be taken.
cd /opt/stack/devstack && source openrc admin admin >/dev/null 2>&1
set -x
openstack flavor create student.small --vcpus 1 --ram 1024 --disk 5 -f value -c id
openstack network create student-network -f value -c id
openstack subnet create student-subnet --network student-network --subnet-range 192.168.10.0/24 --gateway 192.168.10.1 --dns-nameserver 8.8.8.8 -f value -c id
openstack keypair create --public-key ~/.ssh/openstack_key.pub student-key -f value -c name
openstack security group create student-security -f value -c id
openstack security group rule create --proto tcp --dst-port 22 student-security -f value -c id
openstack security group rule create --proto icmp student-security -f value -c id
openstack router add subnet router1 student-subnet
openstack server create --image cirros-0.6.3-x86_64-disk --flavor m1.tiny --network student-network --key-name student-key --security-group student-security --wait student-vm -f value -c status
FIP=$(openstack floating ip create public -f value -c floating_ip_address)
openstack server add floating ip student-vm "$FIP"
openstack volume create --size 1 student-volume -f value -c id
for i in $(seq 30); do [ "$(openstack volume show student-volume -f value -c status)" = available ] && break; sleep 3; done
openstack server add volume student-vm student-volume -f value -c Device
for i in $(seq 60); do openstack console log show student-vm | grep -q "login:" && break; sleep 5; done
openstack server image create --name student-vm-snapshot --wait student-vm -f value -c status
openstack server list
grep ADMIN_PASSWORD= local.conf | cut -d= -f2 > /tmp/tp4_horizon_pw
