#!/usr/bin/env bash
# Execute as stack. Output intentionally excludes token IDs and credentials.
set -euo pipefail
cd /opt/stack/devstack
set +u; source openrc admin admin >/dev/null 2>&1 || true; set -u
set +x
echo '=== Ubuntu and host ==='
date -u +'%Y-%m-%dT%H:%M:%SZ'
cat /etc/os-release | head -6
hostname
hostname -I
nproc
free -h
df -h /
echo '=== Dedicated installer account ==='
id
sudo -n true && echo 'Passwordless sudo: OK'
echo '=== Virtualization ==='
test -c /dev/kvm && echo '/dev/kvm available' || echo 'No /dev/kvm; QEMU emulation configured'
echo '=== DevStack version ==='
git rev-parse HEAD
test -f /opt/stack/tp4-stack-complete && echo 'stack.sh completion marker: PRESENT'
echo '=== Token issuance (ID omitted) ==='
openstack token issue -c expires -f value
echo '=== Service catalogue ==='
openstack service list
echo '=== Images ==='
openstack image list
echo '=== Flavors ==='
openstack flavor list
echo '=== Networks ==='
openstack network list
echo '=== Servers ==='
openstack server list
echo '=== Compute and network services ==='
openstack compute service list
openstack network agent list
echo '=== Horizon HTTP response ==='
host_ip=$(ip -4 route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1);exit}}')
curl --fail --silent --show-error -I "http://$host_ip/dashboard/"
echo 'TP4 CLI verification completed successfully.'
