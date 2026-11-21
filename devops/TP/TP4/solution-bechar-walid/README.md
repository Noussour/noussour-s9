# TP4: OpenStack (DevStack), solution Bechar Walid

| File | Content |
|------|---------|
| `../TP4_Openstack.pdf` | Subject: DevStack installation guide (Ubuntu 24.04) |
| `../TP4_OpenStack_Assignment.pdf` | Subject: homework, 8 exercises (services, images/flavors, network, security, VM, floating IP, Cinder, cleanup) |
| `TP4_OpenStack_Report.pdf` | Report: commands, real outputs, Horizon screenshots, answers to every question |

## Environment

- AWS EC2 m7i-flex.large (2 vCPU, 8 GB RAM, 80 GB gp3), Ubuntu Server 24.04 LTS
- DevStack single node, Neutron with OVN, Cinder with LVM, QEMU emulation (no nested virtualization)

## Rebuilding the report

```
source/scripts/tp4_run.sh ex1 ex2 ex3 ex4 ex5 ex6 ex7 ex8   # on the DevStack VM, as user stack; logs in /opt/stack/tp4-logs
python3 source/build_report.py source/logs source/report.html
# print source/report.html to PDF (headless Chrome --print-to-pdf)
```

- `source/logs/`: raw command outputs for each exercise (token value and admin password redacted)
- `source/shots_c/`: Horizon screenshots, captured with `source/scripts/shoot.mjs` (puppeteer-core) and cropped with `crop.py`
- `source/scripts/tp4_setup.sh`: recreates the resources so the Horizon screenshots can be taken

## Note

After a reboot of the host, `br-ex` loses its address and floating IPs become unreachable. Fix:

```
sudo ip link set br-ex up
sudo ip addr add 172.24.4.1/24 dev br-ex
```
