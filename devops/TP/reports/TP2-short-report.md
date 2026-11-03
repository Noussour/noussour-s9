# TP2 — Short report and question answers

USTHB · DevOps and Cloud Computing · 2026/2027 · 3 November 2026

Student: ____________________ · Provider: Microsoft Azure

**Status:** worked solution, not an executed deployment. All values below are planned or illustrative. The detailed report supplies commands and labeled simulated figures. Actual screenshots and results must come from a real run. The worksheet's first “Q10” is treated as Q1.

## Q1 — Platform and configuration

Planned configuration: Azure, France Central, Ubuntu Server 24.04 LTS, Standard_B1s, 30-GiB Standard HDD disk, VM `tp2-student`, private IP 10.20.1.4, administrator `azureuser`. Azure allocates the real Standard public IPv4 during deployment; 203.0.113.10 is only an example. Verify size availability, credits, quota and the actual image version. SSH/22 and HTTP/80 admit only the workstation's public IPv4 /32.

## Q2 — Local VM versus cloud VM

The VMware VM uses student-managed local hardware and hypervisor settings. Azure provides virtual resources on provider-managed infrastructure and exposes them through cloud APIs. Networking differs: VMware NAT/bridged/host-only adapters versus Azure VNet/NIC/public IP/NSG. Azure usage is metered, and independent disks/IPs can outlive a VM.

## Q3 — IaaS responsibilities

IaaS provides configurable virtual compute, storage and networking. Azure manages the physical datacenter, hardware and virtualization layer. The student manages Linux updates, applications, accounts, keys, firewall policies, data protection and cleanup. Provisioning a VM does not transfer application-security responsibility to the provider.

## Q4 — Restrict SSH

Only the authorized workstation needs administrative TCP 22 access. A /32 source rule reduces scanning and unauthorized connection attempts. Public wildcard access unnecessarily exposes the service. Use a protected private key, verify the server fingerprint, and update the allowed source if the workstation's public IP changes.

## Q5 — Confirm the SSH destination

Compare the SSH fingerprint against the key obtained through authenticated Azure Run Command. In the SSH session, collect `hostname`, `whoami`, `ip a` and `uptime`; expected example identity is tp2-student / azureuser / 10.20.1.4. Correlate those values with Azure inventory. A prompt or username alone is insufficient. These checks have not actually been run against a cloud VM for this document.

## Q6 — Confirm Nginx

Install Nginx, enable it and check `systemctl status nginx --no-pager`, `nginx -t`, its port-80 listener and `curl -I http://127.0.0.1`. Then open the VM's actual `http://<PUBLIC_IP>` from the allowed workstation and capture the welcome page with its address bar. Local HTTP success alone does not prove external reachability. Keep the NSG and any active guest firewall restricted to the intended source.

## Q7 — Cloud characteristics

On-demand self-service is demonstrated by a user-issued Azure CLI deployment that provisions compute through the provider API. Broad network access is demonstrated by SSH and browser access using standard clients. Collect the actual create/status output and remote-session/browser evidence. Listing supported resize options illustrates potential elasticity but does not prove a resize or autoscaling was performed.

## Q8 — Cost estimate and usage

No billing page or subscription usage was inspected, so actual charges and credits are unknown. Before deployment, configure the Azure Pricing Calculator for VM hours, managed disk, Standard public IPv4 and transfer. After the run, inspect Cost Management → Cost analysis at the permitted scope, filtered to `rg-devops-tp2` and the lab dates. Record any permission restriction and reporting delay. No actual cost amount is asserted.

## Q9 — Cleanup

Delete the dedicated resource group containing the VM, disk, NIC, public IP, NSG and VNet; inspect any extra snapshots/load balancers if added. Verify `az group exists -n rg-devops-tp2` returns `false` and that the filtered resource list is empty. A guest shutdown can leave compute allocated; deallocation can still retain billable disks/IPs. No actual resource deletion was performed for this report.

## Required attachments from the real run

1. Portal VM Overview: running state, region and size visible.
2. Real SSH session: `hostname` and `whoami`, with the remote key verified.
3. Real Nginx welcome page at the remote public address.
4. Portal confirmation of cleanup and CLI inventory verification.

Hide identifiers and secrets as required. Simulated terminal/browser illustrations in the detailed report are explanatory figures, not substitutes for these execution records.

Sources: [Azure Linux VM quickstart](https://learn.microsoft.com/en-us/azure/virtual-machines/linux/quick-create-portal?tabs=ubuntu); [VM states and billing](https://learn.microsoft.com/en-us/azure/virtual-machines/states-billing); [Azure Pricing Calculator](https://azure.microsoft.com/en-us/pricing/calculator/).
