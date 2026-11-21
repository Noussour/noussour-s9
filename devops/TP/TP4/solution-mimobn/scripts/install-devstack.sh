#!/usr/bin/env bash
# Execute as the ordinary stack user after VM preparation/reboot.
set -euo pipefail
if [[ $(id -un) != stack || $EUID -eq 0 ]]; then
    echo 'Execute as the non-root stack user, not as root.' >&2; exit 1
fi
cd /opt/stack/devstack
[[ -s local.conf ]] || { echo 'Run prepare-ubuntu.sh first.' >&2; exit 1; }
echo "DevStack source commit: $(git rev-parse HEAD)"
date -u +'%Y-%m-%dT%H:%M:%SZ'
./stack.sh
date -u +'%Y-%m-%dT%H:%M:%SZ'
touch /opt/stack/tp4-stack-complete
