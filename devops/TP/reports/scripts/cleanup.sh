#!/usr/bin/env bash
# Destructive: deletes only a tagged, dedicated lab resource group.
set -euo pipefail
: "${RG:?Set RG to rg-devops-tp1 or rg-devops-tp2}"
case "$RG" in rg-devops-tp1|rg-devops-tp2) ;; *) echo 'Unexpected group; refusing.' >&2; exit 1;; esac
az account show --query '{subscription:name,state:state}' -o table
if [[ $(az group exists -n "$RG" -o tsv) == false ]]; then
  echo 'Group already absent.'
  exit 0
fi
TAG=$(az group show -n "$RG" --query tags.purpose -o tsv)
[[ "$TAG" == devops-lab ]] || { echo 'Missing ownership tag; refusing.' >&2; exit 1; }
az resource list -g "$RG" --query '[].{name:name,type:type,region:location}' -o table
read -r -p "Delete ALL resources above? Type $RG to confirm: " answer
[[ "$answer" == "$RG" ]] || exit 1
az group delete -n "$RG" --yes
az group wait -n "$RG" --deleted --interval 10 --timeout 1800
EXISTS=$(az group exists -n "$RG" -o tsv)
printf 'Group exists after deletion: %s\n' "$EXISTS"
[[ "$EXISTS" == false ]]
