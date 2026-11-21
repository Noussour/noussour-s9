#!/bin/bash
# Runs TP4 assignment exercises 1-7 as user stack, one log file per exercise.
cd /opt/stack/devstack
source openrc admin admin >/dev/null 2>&1
OUT=/opt/stack/tp4-logs
mkdir -p "$OUT"

run() { echo "stack@devstack:~\$ $*"; eval "$@" 2>&1; echo; }
wait_for() { # $1 = command printing a value, $2 = wanted regex, $3 = tries
  for i in $(seq 1 "${3:-60}"); do v=$(eval "$1" 2>/dev/null); [[ "$v" =~ $2 ]] && return 0; sleep 5; done; return 1; }

ex1() {
  run openstack token issue
  run openstack service list
  run openstack endpoint list
  run openstack compute service list
  run openstack network agent list
}

ex2() {
  run openstack image list
  run openstack image show cirros-0.6.3-x86_64-disk -c name -c disk_format -c container_format -c size -c status
  run openstack flavor list
  run openstack flavor create student.small --vcpus 1 --ram 1024 --disk 5
  run openstack flavor show student.small
}

ex3() {
  run openstack network list
  run openstack subnet list
  run openstack router list
  run openstack network create student-network
  run openstack subnet create student-subnet --network student-network --subnet-range 192.168.10.0/24 --gateway 192.168.10.1 --dns-nameserver 8.8.8.8
  run openstack network show student-network
  run openstack subnet show student-subnet
}

ex4() {
  rm -f ~/.ssh/openstack_key ~/.ssh/openstack_key.pub
  run 'ssh-keygen -t ed25519 -f ~/.ssh/openstack_key -N "" | grep -v -i -E "randomart|^[|+]"'
  run openstack keypair create --public-key ~/.ssh/openstack_key.pub student-key
  run openstack keypair list
  run openstack security group create student-security
  run openstack security group rule create --proto tcp --dst-port 22 student-security
  run openstack security group rule create --proto icmp student-security
  run openstack security group rule list student-security
}

ex5() {
  run openstack image list
  run openstack flavor list
  run openstack network list
  run openstack keypair list
  run openstack security group list
  run openstack server create --image cirros-0.6.3-x86_64-disk --flavor m1.tiny --network student-network --key-name student-key --security-group student-security student-vm
  wait_for "openstack server show student-vm -f value -c status" "ACTIVE|ERROR" 60
  run openstack server list
  run openstack server show student-vm
  # wait for the guest to finish booting (QEMU emulation, no nested virt)
  wait_for "openstack console log show student-vm | tail -5" "login:" 60
  run 'openstack console log show student-vm | tail -40'
}

ex6() {
  run openstack server show student-vm -c addresses
  run openstack floating ip list
  run openstack network list --external
  FIP=$(openstack floating ip create public -f value -c floating_ip_address)
  echo "stack@devstack:~\$ openstack floating ip create public"
  openstack floating ip show "$FIP" 2>&1; echo
  run openstack router list
  run openstack router show router1 -c name -c external_gateway_info -c interfaces_info
  # student-network must be attached to router1 for the floating IP to be reachable
  run openstack router add subnet router1 student-subnet
  run openstack server add floating ip student-vm "$FIP"
  sleep 15
  run openstack server show student-vm -c addresses -c status
  run openstack floating ip list
  run ping -c 4 "$FIP"
  run ssh -i ~/.ssh/openstack_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 cirros@"$FIP" "'hostname; ip -4 addr show eth0; ping -c 2 192.168.10.1'"
}

SSHK="-i ~/.ssh/openstack_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20"

# br-ex loses its address after a host reboot; restore it and retest connectivity
ex6b() {
  run ip -4 addr show br-ex
  run sudo ip link set br-ex up
  run sudo ip addr add 172.24.4.1/24 dev br-ex
  run ip -4 addr show br-ex
  run "ip route | grep 172.24.4"
  run ping -c 4 172.24.4.2
  run ssh $SSHK cirros@172.24.4.2 "'hostname; ip -4 addr show eth0; ping -c 2 192.168.10.1'"
}

ex7b() {
  run ssh $SSHK cirros@172.24.4.2 "'lsblk; sudo dmesg | grep -i vdb | tail -3'"
}

ex7() {
  run openstack volume service list
  run openstack volume type list
  run openstack volume list
  run openstack volume create --size 1 student-volume
  wait_for "openstack volume show student-volume -f value -c status" "available|error" 30
  run openstack volume show student-volume
  run openstack server add volume student-vm student-volume
  wait_for "openstack volume show student-volume -f value -c status" "in-use|error" 30
  run openstack volume show student-volume -c name -c status -c size -c attachments
  FIP=$(openstack floating ip list -f value -c "Floating IP Address" -c "Fixed IP Address" | awk '$2 ~ /^192\.168\.10\./ {print $1; exit}')
  run ssh -i ~/.ssh/openstack_key -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=20 cirros@"$FIP" "'lsblk'"
  run openstack server image create --name student-vm-snapshot --wait student-vm
  run openstack image list
  run openstack image show student-vm-snapshot -c name -c status -c disk_format -c size
}

ex8() {
  run openstack server show student-vm -c name -c status
  run openstack server stop student-vm
  wait_for "openstack server show student-vm -f value -c status" "SHUTOFF" 30
  run openstack server show student-vm -c name -c status
  FIP=$(openstack floating ip list -f value -c "Floating IP Address" -c "Fixed IP Address" | awk '$2 ~ /^192\.168\.10\./ {print $1; exit}')
  run openstack server remove volume student-vm student-volume
  wait_for "openstack volume show student-volume -f value -c status" "available" 30
  run openstack server remove floating ip student-vm "$FIP"
  run openstack floating ip delete "$FIP"
  run openstack server delete --wait student-vm
  run openstack volume delete student-volume
  run openstack image delete student-vm-snapshot
  run openstack router remove subnet router1 student-subnet
  run openstack subnet delete student-subnet
  run openstack network delete student-network
  run openstack security group delete student-security
  run openstack keypair delete student-key
  run openstack flavor delete student.small
  sleep 5
  run openstack server list
  run openstack volume list
  run openstack image list
  run openstack network list
  run openstack security group list
  run openstack keypair list
  run openstack floating ip list
}

for e in "$@"; do $e > "$OUT/$e.txt"; echo "done $e"; done
