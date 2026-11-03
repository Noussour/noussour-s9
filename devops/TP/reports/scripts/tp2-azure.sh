#!/usr/bin/env bash
# Reproducible TP2 provisioning. Real execution creates billable resources.
set -euo pipefail
export MSYS_NO_PATHCONV=1
RG=rg-devops-tp2
LOCATION=${LOCATION:-francecentral}
SIZE=${SIZE:-Standard_B1s}
ADMIN=${ADMIN:-azureuser}
VM=tp2-student
KEY=${KEY:-"$HOME/.ssh/devops-tp2"}
IMAGE=${IMAGE:-Canonical:ubuntu-24_04-lts:server:latest}
NSG=nsg-tp2
: "${CLIENT_IP:?Set CLIENT_IP to your workstation public IPv4 address}"
python3 - "$CLIENT_IP" <<'PY'
import ipaddress, sys
a = ipaddress.ip_address(sys.argv[1])
assert a.version == 4 and a.is_global, 'Use your real public IPv4 address, not an example/private address'
PY
az account show --query '{subscription:name,state:state}' -o table
if [[ $(az group exists -n "$RG" -o tsv) == true ]]; then
  echo "Group $RG already exists; inspect it and choose a fresh lab environment." >&2
  exit 1
fi
mkdir -p "$(dirname "$KEY")"
if [[ ! -f "$KEY" ]]; then
  ssh-keygen -t ed25519 -a 64 -f "$KEY" -C devops-tp2
fi
test -s "$KEY.pub"
chmod 600 "$KEY"
echo 'Check SKU availability, quota, image support, and cost before continuing.'
az vm list-skus --location "$LOCATION" --resource-type virtualMachines \
  --size "$SIZE" --all --query '[].{Name:name,Restrictions:restrictions}' -o json
read -r -p "Type CREATE to deploy $VM in $LOCATION: " answer
[[ "$answer" == CREATE ]] || exit 1
az group create -n "$RG" -l "$LOCATION" --tags purpose=devops-lab lab=tp2 -o none
az network vnet create -g "$RG" -n vnet-tp2 --address-prefixes 10.20.0.0/16 \
  --subnet-name subnet-tp2 --subnet-prefixes 10.20.1.0/24 -o none
az network nsg create -g "$RG" -n "$NSG" -o none
for spec in '100 22 Allow-SSH-Student' '110 80 Allow-HTTP-Student'; do
  read -r priority port name <<< "$spec"
  az network nsg rule create -g "$RG" --nsg-name "$NSG" -n "$name" \
    --priority "$priority" --direction Inbound --access Allow --protocol Tcp \
    --source-address-prefixes "$CLIENT_IP/32" --source-port-ranges '*' \
    --destination-address-prefixes '*' --destination-port-ranges "$port" -o none
done
az network public-ip create -g "$RG" -n pip-tp2 --sku Standard \
  --allocation-method Static --version IPv4 -o none
az network nic create -g "$RG" -n nic-tp2 --vnet-name vnet-tp2 \
  --subnet subnet-tp2 --network-security-group "$NSG" \
  --public-ip-address pip-tp2 --private-ip-address 10.20.1.4 -o none
az vm create -g "$RG" -n "$VM" -l "$LOCATION" --nics nic-tp2 \
  --image "$IMAGE" --size "$SIZE" --admin-username "$ADMIN" \
  --authentication-type ssh --ssh-key-values "$KEY.pub" \
  --os-disk-size-gb 30 --storage-sku Standard_LRS --os-disk-name disk-tp2 \
  --tags purpose=devops-lab lab=tp2 -o none
az vm get-instance-view -g "$RG" -n "$VM" \
  --query '{name:name,status:instanceView.statuses[].displayStatus}' -o json
az vm show -g "$RG" -n "$VM" \
  --query '{region:location,size:hardwareProfile.vmSize,image:storageProfile.imageReference}' -o json
PUBLIC_IP=$(az network public-ip show -g "$RG" -n pip-tp2 --query ipAddress -o tsv)
printf '\nNext: verify the VM host-key fingerprint before accepting SSH.\n'
printf 'ssh -i %q %q\n' "$KEY" "$ADMIN@$PUBLIC_IP"
printf 'Browser (from the approved workstation): http://%s\n' "$PUBLIC_IP"
printf 'Follow TP2-report.md to install Nginx, collect evidence, and clean up.\n'
