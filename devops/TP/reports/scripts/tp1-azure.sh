#!/usr/bin/env bash
# Azure adaptation, NOT a VMware/OVA deployment. Creates billable resources.
set -euo pipefail
export MSYS_NO_PATHCONV=1
RG=rg-devops-tp1
LOCATION=${LOCATION:-francecentral}
SIZE=${SIZE:-Standard_B1ms}
ADMIN=${ADMIN:-azureuser}
KEY=${KEY:-"$HOME/.ssh/devops-tp1"}
IMAGE=${IMAGE:-Canonical:ubuntu-24_04-lts:server:latest}
: "${CLIENT_IP:?Set CLIENT_IP to your workstation public IPv4 address}"
python3 - "$CLIENT_IP" <<'PY'
import ipaddress, sys
a = ipaddress.ip_address(sys.argv[1])
assert a.version == 4 and a.is_global, 'Use your real public IPv4, not an example/private address'
PY
az account show --query '{subscription:name,state:state}' -o table
if [[ $(az group exists -n "$RG" -o tsv) == true ]]; then
  echo "Group $RG already exists; inspect it before rerunning." >&2
  exit 1
fi
mkdir -p "$(dirname "$KEY")"
if [[ ! -f "$KEY" ]]; then
  ssh-keygen -t ed25519 -a 64 -f "$KEY" -C devops-tp1
fi
test -s "$KEY.pub"
chmod 600 "$KEY"
az vm list-skus -l "$LOCATION" --resource-type virtualMachines --size "$SIZE" --all \
  --query '[].{Name:name,Restrictions:restrictions}' -o json
read -r -p "Type CREATE for the TP1 Azure adaptation in $LOCATION: " answer
[[ "$answer" == CREATE ]] || exit 1
az group create -n "$RG" -l "$LOCATION" --tags purpose=devops-lab lab=tp1 -o none
az network vnet create -g "$RG" -n vnet-tp1 --address-prefixes 10.10.0.0/16 \
  --subnet-name private --subnet-prefixes 10.10.1.0/24 -o none
az network nsg create -g "$RG" -n nsg-tp1 -o none
az network nsg rule create -g "$RG" --nsg-name nsg-tp1 -n SSH-Student \
  --priority 100 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes "$CLIENT_IP/32" --source-port-ranges '*' \
  --destination-address-prefixes '*' --destination-port-ranges 22 -o none
az network nsg rule create -g "$RG" --nsg-name nsg-tp1 -n SSH-Peer \
  --priority 110 --direction Inbound --access Allow --protocol Tcp \
  --source-address-prefixes 10.10.1.0/24 --source-port-ranges '*' \
  --destination-address-prefixes '*' --destination-port-ranges 22 -o none
az network nsg rule create -g "$RG" --nsg-name nsg-tp1 -n Deny-Other-Inbound \
  --priority 200 --direction Inbound --access Deny --protocol '*' \
  --source-address-prefixes '*' --source-port-ranges '*' \
  --destination-address-prefixes '*' --destination-port-ranges '*' -o none
az network public-ip create -g "$RG" -n pip-tp1 --sku Standard \
  --allocation-method Static --version IPv4 -o none
az network nic create -g "$RG" -n nic-tp1-01 --vnet-name vnet-tp1 --subnet private \
  --network-security-group nsg-tp1 --private-ip-address 10.10.1.4 \
  --public-ip-address pip-tp1 -o none
az vm create -g "$RG" -n LinuxLite-01 -l "$LOCATION" --nics nic-tp1-01 \
  --image "$IMAGE" --size "$SIZE" --admin-username "$ADMIN" \
  --authentication-type ssh --ssh-key-values "$KEY.pub" \
  --storage-sku Standard_LRS --os-disk-size-gb 30 --os-disk-name disk-tp1-01 \
  --tags purpose=devops-lab lab=tp1 -o none
PUBLIC_IP=$(az network public-ip show -g "$RG" -n pip-tp1 --query ipAddress -o tsv)
printf '\nVM1 public IP: %s\n' "$PUBLIC_IP"
printf 'Connect: ssh -i %q %q\n' "$KEY" "$ADMIN@$PUBLIC_IP"
printf 'Continue with the Azure adaptation in TP1-report.md.\n'
printf 'VM2 cloning and baseline recovery are deliberately separate, observable steps.\n'
