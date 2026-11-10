#!/usr/bin/env bash
# Execute as root ONLY on the dedicated Ubuntu 24.04 lab VM.
set -euo pipefail
if [[ $EUID -ne 0 ]]; then echo 'Run this preparation script with sudo.' >&2; exit 1; fi
source /etc/os-release
if [[ $ID != ubuntu || $VERSION_ID != 24.04 ]]; then
    echo 'This lab requires a dedicated Ubuntu 24.04 installation.' >&2; exit 1
fi
if [[ -e /opt/stack/devstack/local.conf ]]; then
    echo 'Existing DevStack configuration found; refusing to overwrite it.' >&2; exit 1
fi
export DEBIAN_FRONTEND=noninteractive
# Extra headroom for the smaller 8-GB lab VM; swap is slower than RAM.
if ! swapon --show --noheadings | grep -q .; then
    fallocate -l 4G /swapfile-tp4
    chmod 600 /swapfile-tp4
    mkswap /swapfile-tp4
    swapon /swapfile-tp4
    printf '%s\n' '/swapfile-tp4 none swap sw 0 0' >> /etc/fstab
fi
apt-get update
apt-get -o Dpkg::Options::=--force-confold upgrade -y
apt-get install -y git curl wget openssl python3-venv
id stack >/dev/null 2>&1 || useradd -s /bin/bash -d /opt/stack -m stack
chmod +x /opt/stack
printf '%s\n' 'stack ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/stack
chmod 440 /etc/sudoers.d/stack
visudo -cf /etc/sudoers.d/stack
sudo -u stack -H git clone https://opendev.org/openstack/devstack /opt/stack/devstack
host_ip=$(ip -4 route get 1.1.1.1 | awk '{for(i=1;i<=NF;i++) if($i=="src") {print $(i+1);exit}}')
libvirt_type=qemu
modprobe kvm_intel 2>/dev/null || modprobe kvm_amd 2>/dev/null || true
if [[ -c /dev/kvm ]]; then libvirt_type=kvm; fi
# This password is deliberately generated on the VM, never stored in Git.
admin_password=$(openssl rand -hex 16)
install -o stack -g stack -m 600 /dev/null /opt/stack/tp4-admin-password.txt
printf '%s\n' "$admin_password" > /opt/stack/tp4-admin-password.txt
install -o stack -g stack -m 600 /dev/null /opt/stack/devstack/local.conf
cat > /opt/stack/devstack/local.conf <<EOF
[[local|localrc]]
ADMIN_PASSWORD=$admin_password
DATABASE_PASSWORD=\$ADMIN_PASSWORD
RABBIT_PASSWORD=\$ADMIN_PASSWORD
SERVICE_PASSWORD=\$ADMIN_PASSWORD
HOST_IP=$host_ip
LIBVIRT_TYPE=$libvirt_type
LOGFILE=/opt/stack/logs/stack.sh.log
LOG_COLOR=False
EOF
install -d -o stack -g stack /opt/stack/logs
echo "TP4 preparation complete; HOST_IP=$host_ip, LIBVIRT_TYPE=$libvirt_type"
echo 'Password saved privately on the VM; it is not printed in this log.'
if [[ -e /var/run/reboot-required ]]; then echo 'REBOOT_REQUIRED'; fi
