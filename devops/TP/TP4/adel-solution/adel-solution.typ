#set document(title: "OpenStack: Cloud Resource Management and VM Deployment", author: "Adel HADJ ARAB")
#set page(paper: "a4", margin: (x: 2cm, y: 1.8cm), numbering: "1 / 1",
  header: context if counter(page).get().first() > 1 [
    #set text(8pt, fill: luma(120))
    Adel HADJ ARAB #h(1fr) OpenStack: Cloud Resource Management and VM Deployment
  ])
#set text(font: "New Computer Modern", size: 10.5pt)
#set par(justify: true, leading: 0.62em, spacing: 0.9em)
#let accent = rgb("#1f4e79")
#show heading.where(level: 1): it => block(above: 1.6em, below: 0.8em, width: 100%)[
  #text(13pt, weight: "bold", fill: accent, it.body)
  #v(-0.5em)
  #line(length: 100%, stroke: 0.6pt + accent)
]
#show raw.where(block: true): it => block(fill: luma(245), stroke: (left: 2pt + accent), inset: (x: 8pt, y: 6pt), width: 100%, text(size: 8.5pt, it))
#show figure: set block(above: 0.9em, below: 1em)
#show figure.caption: set text(size: 8.5pt, fill: luma(70))

#let shot(file, caption, width: 75%) = figure(
  box(stroke: 0.4pt + luma(170), image("screenshots/" + file, width: width)),
  caption: caption,
)
#let q(body) = text(weight: "bold", fill: accent, body)

#align(center)[
  #block(text(15pt, weight: "bold", fill: accent)[OpenStack: Cloud Resource Management and VM Deployment])
  #block(above: 0.5em, text(11pt)[Adel HADJ ARAB])
  #block(above: 0.4em, text(9.5pt, fill: luma(90))[DevOps and Cloud Computing · USTHB · 2026/2027])
]
#v(0.4em)

#block(fill: luma(245), inset: 9pt, radius: 3pt, width: 100%)[
  *Environment.* DevStack (Horizon 27.1.0) on one AWS EC2 Ubuntu instance (`ip-172-31-19-63`), all services on the same host, `admin` project. Each step was done in the Horizon dashboard; the matching `openstack` CLI command is given each time, and each screenshot is the Horizon view of that command.
]

= Exercise 1: Explore the OpenStack environment

```sh
source openrc admin admin
openstack token issue
openstack service list
openstack endpoint list
openstack compute service list
openstack network agent list
```

#shot("01-services.png", [Services and public endpoints (`service list` / `endpoint list`).])

#grid(columns: 2, gutter: 8pt,
  shot("02-compute-services.png", [`compute service list`], width: 100%),
  shot("04-network-agents.png", [`network agent list`], width: 100%),
)

#q[Roles.] *Keystone*: identity; authenticates users, issues tokens, manages projects/roles and the service catalog. *Nova*: compute; creates, schedules and manages instances. *Neutron*: networking; networks, subnets, routers, floating IPs, security groups. *Glance*: images used to boot instances (and snapshots). *Cinder*: persistent block volumes.

#q[Who does what.] Identity and authentication: Keystone. Compute: Nova (with Placement). Networking: Neutron. Images: Glance.

#q[Services and agents found.] 7 services: keystone, nova, nova_legacy, neutron, glance, placement, cinder (all in RegionOne). Compute: nova-scheduler, 2 × nova-conductor, nova-compute, all Enabled/Up. Network agents: ovn-controller and neutron-ovn-agent, Up (the ML2/OVN back end does DHCP, routing and NAT itself, so there are no separate DHCP/L3 agents). Cinder: cinder-scheduler and cinder-volume (lvmdriver-1), Up. Nothing is missing or down; Swift and Heat are simply not installed in this DevStack.

#q[`openstack token issue`.] It prints the token `id` (sent as `X-Auth-Token` with every API call), its `expires` date (1 hour by default), and the `project_id` and `user_id` it belongs to. The token is a secret and is not shown here.

= Exercise 2: Images and flavors

```sh
openstack image list
openstack flavor list
openstack flavor create student.small --vcpus 1 --ram 1024 --disk 5
```

#shot("06-images.png", [`image list`: `cirros-0.6.3-x86_64-disk`, QCOW2, 20.69 MB (the snapshot from Exercise 7 also appears).])

#shot("07-flavors.png", [`flavor list`, including the created `student.small` (1 vCPU, 1 GB RAM, 5 GB disk).], width: 65%)

Flavors go from `m1.nano` (1 vCPU, 192 MB, 1 GB) and `m1.tiny` (1 vCPU, 512 MB, 1 GB) up to `m1.xlarge` (8 vCPU, 16 GB, 160 GB); vCPU, RAM and disk grow together, ephemeral and swap are 0.

#q[Choice.] Image `cirros-0.6.3-x86_64-disk` (the only image, a minimal Linux) with flavor `m1.tiny`: the 20 MB image fits in 1 GB of disk and 512 MB RAM is enough for CirrOS while using little of the host.

#q[Image vs flavor.] The image is the content of the root disk (OS and files); the flavor is the hardware size (vCPU, RAM, disk). Yes, many instances can use the same image with different flavors, if the flavor disk is at least the image's minimum size.

= Exercise 3: Private network and subnet

Existing subnets: `public` 172.24.4.0/24, `private` 10.0.0.0/26, `shared` 192.168.233.0/24, so 192.168.10.0/24 does not overlap.

```sh
openstack network create student-network
openstack subnet create student-subnet --network student-network \
  --subnet-range 192.168.10.0/24 --gateway 192.168.10.1 --dns-nameserver 8.8.8.8
```

#grid(columns: 2, gutter: 8pt,
  shot("09-network-detail.png", [`network show student-network`: Active, UP, geneve.], width: 100%),
  shot("10-subnet-detail.png", [`subnet show student-subnet`: 192.168.10.0/24, gateway .1, DHCP on, DNS 8.8.8.8.], width: 100%),
)

#q[Neutron.] Networking as a service: tenants create isolated virtual networks, subnets, routers, floating IPs and security groups through an API (here with OVN, Geneve overlay, MTU 1442).

#q[Network vs subnet.] A network is an isolated layer-2 segment (virtual switch); a subnet is an IP block on that network with its gateway, DHCP and DNS settings. One network can carry several subnets.

#q[Range, gateway, DNS.] The range gives the addresses for ports (allocation pool .2–.254 by DHCP); the gateway (192.168.10.1) is the router address used to leave the subnet; the DNS server (8.8.8.8) is given to instances by DHCP for name resolution.

#q[Why a network?] Without a port on a network the VM gets no IP: no SSH, no metadata service (so no key injection), no Internet, no communication with other VMs.

= Exercise 4: Key pair and security group

```sh
ssh-keygen -t ed25519 -f ~/.ssh/openstack_key
openstack keypair create --public-key ~/.ssh/openstack_key.pub student-key
openstack security group create student-security
openstack security group rule create --proto tcp --dst-port 22 student-security
openstack security group rule create --proto icmp student-security
```

#grid(columns: 2, gutter: 8pt,
  shot("11-keypairs.png", [`keypair list`: `student-key` (only the public part is stored).], width: 100%),
  shot("12-security-rules.png", [`security group rule list student-security`.], width: 100%),
)

#q[SSH key pair.] Two linked keys for passwordless login. The public key is stored in OpenStack and injected into the VM (`authorized_keys`); it can be shared. The private key stays secret on the client and proves identity; it must never be shared.

#q[Security group.] A stateful virtual firewall on the instance ports: only traffic matching an allow rule enters; replies to allowed traffic are accepted automatically.

#q[Allowed traffic.] Ingress TCP 22 from 0.0.0.0/0 (SSH) and ingress ICMP from 0.0.0.0/0 (ping); the two default egress rules allow all outgoing IPv4/IPv6 traffic.

#q[Closed ports.] Every open port is attack surface (scans, brute force, exploits). Least privilege: open only what is needed, ideally from a restricted source prefix.

= Exercise 5: Launch a virtual machine

```sh
openstack server create --image cirros-0.6.3-x86_64-disk --flavor m1.tiny \
  --network student-network --key-name student-key \
  --security-group student-security student-vm
openstack server show student-vm
openstack console log show student-vm
```

#shot("13-instances.png", [`server list`: `student-vm` Active, Running.])

#grid(columns: 2, gutter: 8pt,
  shot("14-instance-overview.png", [`server show student-vm`.], width: 100%),
  shot("15-console-log.png", [`console log show student-vm`: CirrOS booted, eth0 = 192.168.10.241/24, route via 192.168.10.1.], width: 100%),
)

#q[Result.] Status *ACTIVE* (Running), image `cirros-0.6.3-x86_64-disk`, flavor `m1.tiny` (1 vCPU, 512 MB, 1 GB), network `student-network`, fixed IP *192.168.10.241* (floating 172.24.4.155 added in Exercise 6), key `student-key`, group `student-security`.

#q[Instance.] A virtual machine running in the cloud, built from an image and a flavor, attached to networks and managed by Nova.

#q[Role of Nova.] nova-api checks the request with Keystone; nova-scheduler (with Placement) picks a host with enough resources; nova-conductor handles the database; nova-compute gets the image from Glance, a port from Neutron and starts the VM on the hypervisor (libvirt/KVM).

#q[ACTIVE.] The build succeeded and the VM is running on the hypervisor. It does not prove the guest has finished booting or is reachable.

#q[Why not ACTIVE?] (1) "No valid host": not enough RAM/disk/vCPU on any compute node, or quota exceeded → ERROR. (2) Image or network problem: flavor disk smaller than the image, Glance download failure, or Neutron cannot bind the port.

= Exercise 6: Connectivity and floating IP

Fixed IP of `student-vm`: *192.168.10.241*. To test it, use a machine on the same network (another instance on `student-network`, or the DevStack host through the router): `ping 192.168.10.241` and `ssh -i ~/.ssh/openstack_key cirros@192.168.10.241`; ICMP and TCP 22 are allowed.

The environment has an external network `public` (172.24.4.0/24), so the conditional part was done. A floating IP needs a router from the subnet to `public`, so `student-router` was created first:

```sh
openstack router create student-router
openstack router set student-router --external-gateway public
openstack router add subnet student-router student-subnet
openstack floating ip create public
openstack server add floating ip student-vm 172.24.4.155
ssh -i ~/.ssh/openstack_key cirros@172.24.4.155
```

#grid(columns: 2, gutter: 8pt,
  shot("20-router-interfaces.png", [`student-router`: gateway on `public` + interface 192.168.10.1.], width: 100%),
  shot("16-floating-ips.png", [`floating ip list`: 172.24.4.155 → 192.168.10.241, Active.], width: 100%),
)

#shot("21-topology.png", [Topology: `student-vm` on `student-network`, through `student-router` to `public`.], width: 55%)

DevStack's `public` network only exists inside the EC2 host (`br-ex`), so 172.24.4.155 is reachable from the DevStack host, not from the Internet. CirrOS user: `cirros`.

#q[Fixed vs floating IP.] A fixed IP is the private address from the tenant subnet, kept by the port for the life of the instance. A floating IP is an external address NATed by the router to a fixed IP; it can be moved between instances and released separately.

#q[ACTIVE but no SSH.] Port 22 not allowed, no route (no router or floating IP), guest still booting or sshd down, key not injected (metadata unreachable) or wrong user, or a firewall between client and external network.

#q[Floating IP unavailable in DevStack.] It needs an external provider network, a free address pool and a router gateway; a local install may have no `public` network/bridge, the floating range may not be routed on the LAN, or the pool may be exhausted.

#q[Security group and network.] The network config (subnet, router, gateway, NAT) decides if packets can *reach* the VM; the security group decides if they are *allowed in*. Both must be right.

= Exercise 7: Block storage and snapshots

Cinder is available (cinder-scheduler and cinder-volume Up, volume types `lvmdriver-1` and `__DEFAULT__`), so the conditional part was done.

```sh
openstack volume service list
openstack volume type list
openstack volume create --size 1 student-volume
openstack server add volume student-vm student-volume
openstack server image create --name student-vm-snapshot student-vm
openstack image list
```

#grid(columns: 2, gutter: 8pt,
  shot("03-volume-services.png", [`volume service list`], width: 100%),
  shot("18-volume-types.png", [`volume type list`], width: 100%),
)

#shot("17-volumes.png", [`volume list`: `student-volume`, 1 GiB, In-use, attached to `student-vm` on `/dev/vdb`. The console log in Exercise 5 shows the guest detecting the new 1 GiB `vdb` disk.])

#shot("19-images-snapshot.png", [`image list`: `student-vm-snapshot`, type Snapshot, QCOW2, 51 MB.])

#q[Cinder.] Block storage as a service: creates volumes on a back end (here LVM), attaches/detaches them to instances, manages volume snapshots and backups.

#q[Root disk vs volume.] The root disk (`vda`, from the flavor) is ephemeral: created from the image and deleted with the instance. A Cinder volume (`vdb`) is persistent: it survives the instance and can be attached to another one.

#q[Instance snapshot.] A copy of the root disk saved as a Glance image. Useful as a backup, to roll back after a bad change, or to launch identical copies. Attached volumes are not included.

#q[No Cinder.] `volume service list` would be empty or fail, so no volume can be created; only ephemeral disks exist and data is lost with the instance. Instance snapshots still work (Glance).

= Exercise 8: Lifecycle and cleanup

`openstack server show student-vm` → status ACTIVE, Running (instance overview in Exercise 5).

#q[Stop vs delete.] Stopping (`server stop`) shuts the VM down (SHUTOFF) but keeps its disk, IP, ports, volumes and quota; it can be started again. Deleting (`server delete`) destroys the VM and its root disk and frees its IP and resources, permanently; attached volumes are only detached.

#q[Created resources.] Instance `student-vm`, snapshot `student-vm-snapshot`, volume `student-volume`, floating IP 172.24.4.155, key pair `student-key`, security group `student-security`, router `student-router`, network `student-network` / subnet `student-subnet`, flavor `student.small`. Pre-existing resources (cirros image, default flavors, `public`/`private`/`shared` networks, `router1`, `default` groups) were kept.

Deletion in dependency order:

```sh
openstack server remove volume student-vm student-volume
openstack volume delete student-volume
openstack floating ip delete 172.24.4.155
openstack server delete student-vm
openstack image delete student-vm-snapshot
openstack router remove subnet student-router student-subnet
openstack router delete student-router
openstack network delete student-network        # also deletes student-subnet
openstack security group delete student-security
openstack keypair delete student-key
openstack flavor delete student.small
```

A volume cannot be deleted while attached, and a subnet cannot be deleted while a router or VM port uses it.

#shot("22-after-cleanup.png", [After cleanup: 0 instances, 0 volumes, 0 floating IPs, 0 routers in the project.], width: 60%)
