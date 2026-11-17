"""Build the TP4 OpenStack assignment report (HTML) from captured DevStack logs."""
import html
import re
import sys
from pathlib import Path

LOGS = Path(sys.argv[1])
OUT = Path(sys.argv[2])
PROMPT = "stack@devstack:~$ "
FIT = 124  # characters that fit at the base font size
MAXW = 192  # hard limit; wider lines are truncated (font scales down to fit up to this)


def blocks(name):
    """Split a log into (command, output_lines) pairs."""
    text = (LOGS / f"{name}.txt").read_text()
    res = []
    for chunk in text.split(PROMPT)[1:]:
        lines = chunk.rstrip("\n").split("\n")
        res.append((lines[0], [l for l in lines[1:]]))
    return res


def find(name, pattern, nth=0):
    hits = [b for b in blocks(name) if re.search(pattern, b[0])]
    return hits[nth]


def redact(line):
    line = re.sub(r"(\| id\s+\| )(gAAAA\S{12})\S+", lambda m: m.group(1) + m.group(2) + "...[redacted]", line)
    line = re.sub(r"(\| adminPass\s+\| )\S+", r"\1[redacted]", line)
    return line


def term(name, pattern, nth=0, keep=None, note=None, tail=None):
    """Render one captured command and its output as a terminal block.

    keep: regex; for key/value tables, keep only border lines, header and rows whose field matches.
    tail: keep only the last N output lines.
    """
    cmd, out = find(name, pattern, nth)
    trimmed = False
    if keep:
        # parse the Field/Value table, keep matching fields, and redraw it at its new width
        rx = re.compile(keep)
        rows, cur_keep = [], False
        for l in out:
            m = re.match(r"\| (.*?)\s*\| (.*?)\s*\|$", l)
            if not m:
                continue
            field, value = m.group(1), m.group(2)
            if field == "Field":
                continue
            if field:
                cur_keep = bool(rx.search(field))
            if cur_keep:
                rows.append((field, value))
            else:
                trimmed = True
        vmax = FIT - 30
        rows = [(f, redact(f"| {f} | {v}").split(" | ", 1)[1]) for f, v in rows]
        rows = [(f, v if len(v) <= vmax else v[: vmax - 3] + "...") for f, v in rows]
        if any(len(v) == vmax and v.endswith("...") for _, v in rows):
            trimmed = True
        fw = max([len(f) for f, _ in rows] + [5])
        vw = max([len(v) for _, v in rows] + [5])
        border = f"+-{'-' * fw}-+-{'-' * vw}-+"
        out = [border, f"| {'Field':<{fw}} | {'Value':<{vw}} |", border]
        out += [f"| {f:<{fw}} | {v:<{vw}} |" for f, v in rows] + [border]
    if tail and len(out) > tail:
        out = out[-tail:]
        trimmed = True
    lines = []
    for l in out:
        l = redact(l)
        if len(l) > MAXW:
            l = l[: MAXW - 3] + "..."
            trimmed = True
        lines.append(l)
    while lines and not lines[-1].strip():
        lines.pop()
    body = "\n".join(html.escape(l) for l in lines) or '<span class="dim">(empty output)</span>'
    if len(cmd) > FIT:
        cmd = re.sub(r" (--\S|-o |cirros@)", lambda m: " \\\n    " + m.group(1), cmd)
    width = max([len(l) for l in lines] + [FIT])
    size = max(4.2, 6.6 * FIT / width)
    caption = note or ""
    if trimmed:
        caption = (caption + " " if caption else "") + "Output trimmed for width or to the relevant fields."
    cap = f'<div class="cap">{html.escape(caption)}</div>' if caption else ""
    return (f'<figure class="term"><div class="bar"><i></i><i></i><i></i><span>stack@devstack: ~ (DevStack VM)</span></div>'
            f'<pre style="font-size:{size:.2f}pt"><span class="p">stack@devstack:~$</span> <span class="c">{html.escape(cmd)}</span>\n{body}</pre>{cap}</figure>')


T = term
FIG = [0]


def shot(name, caption, url):
    """Embed a real Horizon screenshot in a browser frame with a numbered caption."""
    FIG[0] += 1
    return (f'<figure class="shot"><div class="url"><i></i><i></i><i></i><span>{html.escape(url)}</span></div>'
            f'<img src="shots_c/{name}.jpg" alt="{html.escape(caption)}">'
            f'<figcaption><b>Figure {FIG[0]}.</b> {html.escape(caption)}</figcaption></figure>')


H = "http://51.20.94.39/dashboard"

DIAGRAM = """
<figure class="diagram">
<svg viewBox="0 0 760 330" xmlns="http://www.w3.org/2000/svg" font-family="Helvetica, Arial, sans-serif">
  <defs><marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M0,0 L10,5 L0,10 z" fill="#5b6475"/></marker></defs>
  <rect x="10" y="120" width="110" height="70" rx="10" fill="#f1f3f7" stroke="#9aa3b2"/>
  <text x="65" y="150" text-anchor="middle" font-size="13" font-weight="700" fill="#1d2330">Laptop</text>
  <text x="65" y="168" text-anchor="middle" font-size="10" fill="#5b6475">SSH :22, Horizon :80</text>
  <line x1="120" y1="155" x2="160" y2="155" stroke="#5b6475" stroke-width="1.6" marker-end="url(#ar)"/>
  <rect x="165" y="10" width="585" height="310" rx="14" fill="#fff" stroke="#c8102e" stroke-width="1.6"/>
  <text x="180" y="32" font-size="12" font-weight="700" fill="#c8102e">AWS EC2 m7i-flex.large, Ubuntu 24.04, DevStack (single node)</text>
  <g font-size="11" font-weight="700" fill="#fff">
    <rect x="180" y="45" width="82" height="30" rx="6" fill="#3b6fb6"/><text x="221" y="64" text-anchor="middle">Keystone</text>
    <rect x="270" y="45" width="70" height="30" rx="6" fill="#3b6fb6"/><text x="305" y="64" text-anchor="middle">Nova</text>
    <rect x="348" y="45" width="78" height="30" rx="6" fill="#3b6fb6"/><text x="387" y="64" text-anchor="middle">Neutron</text>
    <rect x="434" y="45" width="70" height="30" rx="6" fill="#3b6fb6"/><text x="469" y="64" text-anchor="middle">Glance</text>
    <rect x="512" y="45" width="70" height="30" rx="6" fill="#3b6fb6"/><text x="547" y="64" text-anchor="middle">Cinder</text>
    <rect x="590" y="45" width="78" height="30" rx="6" fill="#3b6fb6"/><text x="629" y="64" text-anchor="middle">Placement</text>
    <rect x="676" y="45" width="64" height="30" rx="6" fill="#6b7686"/><text x="708" y="64" text-anchor="middle">Horizon</text>
  </g>
  <rect x="180" y="100" width="560" height="26" rx="6" fill="#e6f4ea" stroke="#3a9d5d"/>
  <text x="190" y="118" font-size="11" fill="#1d2330"><tspan font-weight="700">public</tspan> (external, 172.24.4.0/24) via OVS bridge br-ex 172.24.4.1</text>
  <line x1="390" y1="126" x2="390" y2="160" stroke="#3a9d5d" stroke-width="2"/>
  <rect x="330" y="160" width="120" height="40" rx="8" fill="#fff4e0" stroke="#e39b17"/>
  <text x="390" y="178" text-anchor="middle" font-size="12" font-weight="700" fill="#1d2330">router1</text>
  <text x="390" y="193" text-anchor="middle" font-size="9.5" fill="#5b6475">SNAT + floating IP NAT</text>
  <line x1="390" y1="200" x2="390" y2="226" stroke="#e39b17" stroke-width="2"/>
  <rect x="180" y="226" width="560" height="26" rx="6" fill="#e8effa" stroke="#3b6fb6"/>
  <text x="190" y="244" font-size="11" fill="#1d2330"><tspan font-weight="700">student-network</tspan> / student-subnet 192.168.10.0/24 (Geneve overlay, gw .1, DHCP)</text>
  <line x1="300" y1="252" x2="300" y2="270" stroke="#3b6fb6" stroke-width="2"/>
  <rect x="220" y="270" width="160" height="40" rx="8" fill="#14181f"/>
  <text x="300" y="287" text-anchor="middle" font-size="12" font-weight="700" fill="#fff">student-vm (CirrOS)</text>
  <text x="300" y="302" text-anchor="middle" font-size="9.5" fill="#aab2c0">m1.tiny, student-security</text>
  <line x1="380" y1="290" x2="470" y2="290" stroke="#5b6475" stroke-width="1.4" stroke-dasharray="4 3"/>
  <rect x="470" y="272" width="130" height="36" rx="8" fill="#f1f3f7" stroke="#9aa3b2"/>
  <text x="535" y="288" text-anchor="middle" font-size="11" font-weight="700" fill="#1d2330">student-volume</text>
  <text x="535" y="301" text-anchor="middle" font-size="9.5" fill="#5b6475">1 GB Cinder LVM, /dev/vdb</text>
  <text x="620" y="180" font-size="10" fill="#5b6475">floating IP 172.24.4.x</text>
  <text x="620" y="194" font-size="10" fill="#5b6475">maps 1:1 to fixed IP</text>
  <text x="620" y="208" font-size="10" fill="#5b6475">192.168.10.x</text>
</svg>
<figcaption><b>Architecture.</b> Lab environment and the resources created in this assignment.</figcaption>
</figure>"""
S = []  # report sections

S.append(f"""
<header class="cover">
  <div class="school">USTHB, Computer Science Department. 5th Year Software Engineering, 2026/2027. DevOps and Cloud Computing</div>
  <h1>TP4: OpenStack, Cloud Resource Management and VM Deployment</h1>
  <div class="who">BECHAR Walid, Group 2</div>
</header>

<h2>Environment</h2>
<p>All exercises were run on our own DevStack installation (from TP4) as the <code>stack</code> user, after
<code>source openrc admin admin</code>. The Ubuntu host is a cloud virtual machine:</p>
<table class="grid">
<tr><th>Host</th><td>AWS EC2 m7i-flex.large (eu-north-1)</td></tr>
<tr><th>Resources</th><td>2 vCPU, 8 GB RAM (+7 GB swap), 80 GB SSD</td></tr>
<tr><th>Operating system</th><td>Ubuntu Server 24.04 LTS</td></tr>
<tr><th>OpenStack</th><td>DevStack (master), single node, Neutron with OVN, Cinder with LVM backend</td></tr>
<tr><th>Hypervisor</th><td>libvirt/QEMU in software emulation (the host has no nested VT-x)</td></tr>
</table>
<p>Every create operation was verified with the matching <code>list</code> or <code>show</code> command.
The terminal figures are the exact command outputs from this environment. Very wide tables were trimmed to the
relevant fields, and secrets (token value, generated admin password) are redacted.</p>
{DIAGRAM}
<p><b>About the dashboard screenshots.</b> The figures labelled <i>Figure N</i> are real captures of the Horizon
dashboard of the same DevStack. After cleanup (Exercise 8), I recreated the same resources with the same commands
to capture them in Horizon, then cleaned up again. That second instance received the fixed IP
<code>192.168.10.175</code> and the floating IP <code>172.24.4.86</code>; the CLI outputs show the first run
(<code>192.168.10.112</code> and <code>172.24.4.2</code>).</p>
{shot("00-login", "Horizon login page of our DevStack (Default domain, user admin).", H + "/auth/login/")}
{shot("01-overview", "Project overview after login: quota usage for compute, volume and network resources.", H + "/project/")}
""")



# ---------------------------------------------------------------- Exercise 1
S.append(f"""
<h2 class="ex">Exercise 1: Explore the OpenStack environment</h2>
<p><b>What I did.</b> I loaded the admin credentials and ran the five inspection commands.</p>
{T("ex1", r"token issue", keep=r".")}
{T("ex1", r"service list$")}
{T("ex1", r"endpoint list")}
{T("ex1", r"compute service list")}
{T("ex1", r"network agent list")}
{shot("02-services", "Admin, System Information: registered services and their public endpoints.", H + "/admin/info/")}
{shot("03-compute-services", "Compute services (nova-scheduler, nova-conductor, nova-compute) all enabled and up.", H + "/admin/info/?tab=system_info__nova_services")}
{shot("04-network-agents", "Network agents: OVN controller gateway agent and OVN Neutron agent, both alive.", H + "/admin/info/?tab=system_info__network_agents")}
<h3>Interpretation</h3>
<ul>
<li><b>Keystone</b> is the identity service: it authenticates users, issues tokens, and keeps the catalog of
services and endpoints. <b>Nova</b> manages the lifecycle of compute instances (create, schedule, start, stop,
delete). <b>Neutron</b> provides networking as a service: networks, subnets, routers, ports, floating IPs and
security groups. <b>Glance</b> stores and serves virtual machine images. <b>Cinder</b> provides persistent block
storage volumes that can be attached to instances.</li>
<li>Identity and authentication are handled by <b>Keystone</b>. Compute is managed by <b>Nova</b> (with
<b>Placement</b> tracking resource inventory), networking by <b>Neutron</b>, and images by <b>Glance</b>.</li>
<li>The service catalog contains nova, neutron, glance, placement, keystone and cinder, plus
<code>nova_legacy</code>, which is the old compute v2 endpoint kept for compatibility. Each service has a public
endpoint on the host IP. All Nova services (scheduler, two conductors, compute) are <code>enabled</code> and
<code>up</code>. Neutron uses the OVN backend, so instead of the classic L3/DHCP/OVS agents it reports an
<code>ovn-controller</code> gateway agent and the <code>neutron-ovn-agent</code>, both alive. Horizon is not in the
catalog because it is a web front end, not an API service. No expected service is missing or down.</li>
<li><code>openstack token issue</code> displays the token's expiry time (one hour later), the token ID itself
(the bearer credential sent in the <code>X-Auth-Token</code> header), and the project and user the token is scoped
to. The token value is redacted here because it grants admin access until it expires.</li>
</ul>
""")

# ---------------------------------------------------------------- Exercise 2
S.append(f"""
<h2 class="ex">Exercise 2: Inspect images and flavors</h2>
<p><b>What I did.</b> I listed images and flavors, inspected the only image, and created the optional
<code>student.small</code> flavor.</p>
{T("ex2", r"image list")}
{T("ex2", r"image show")}
{T("ex2", r"flavor list")}
{T("ex2", r"flavor create")}
{T("ex2", r"flavor show")}
{shot("07-flavors", "Admin, Flavors: vCPU, RAM and disk of every flavor, including our student.small.", H + "/admin/flavors/")}
<h3>Interpretation</h3>
<ul>
<li>One image is available: <code>cirros-0.6.3-x86_64-disk</code>, in <b>qcow2</b> disk format with a
<b>bare</b> container, about 21 MB. CirrOS is a minimal Linux distribution made for testing clouds.</li>
<li>Flavors range from <code>m1.nano</code> (1 vCPU, 192 MB RAM, 1 GB disk) up to <code>m1.xlarge</code>
(8 vCPU, 16 GB RAM, 160 GB disk). The <code>m1.*</code> series doubles RAM and disk at each step. The
<code>ds*</code> flavors give more disk for a given RAM, and <code>cirros256</code> is sized for CirrOS.</li>
<li><b>Choice:</b> image <code>cirros-0.6.3-x86_64-disk</code> with flavor <code>m1.tiny</code> (1 vCPU,
512 MB, 1 GB). CirrOS needs very little memory and its disk fits in 1 GB. Our host has only 8 GB RAM and runs
guests under software emulation, so the smallest comfortable flavor is the right choice. Larger flavors such as
<code>m1.large</code> or <code>m1.xlarge</code> could not even be scheduled on this host.</li>
<li>The optional flavor <code>student.small</code> (1 vCPU, 1024 MB, 5 GB) was created successfully and is
public.</li>
</ul>
<p><b>Image vs flavor.</b> An <i>image</i> is the content: a disk template containing the operating system that
becomes the instance's root disk. A <i>flavor</i> is the size: the amount of vCPU, RAM and disk allocated to the
instance. They are independent, so yes, several instances can use the same image with different flavors (for
example CirrOS on <code>m1.tiny</code> and on <code>student.small</code>), as long as the flavor's disk is at least
the image's minimum disk size.</p>
""")

# ---------------------------------------------------------------- Exercise 3
S.append(f"""
<h2 class="ex">Exercise 3: Create a private network and subnet</h2>
<p><b>What I did.</b> I first inspected the existing networks. The existing IPv4 subnets are
<code>10.0.0.0/26</code> (private), <code>172.24.4.0/24</code> (public) and <code>192.168.233.0/24</code>
(shared), so <code>192.168.10.0/24</code> does not overlap and I used it as suggested.</p>
{T("ex3", r"network list")}
{T("ex3", r"subnet list")}
{T("ex3", r"router list")}
{T("ex3", r"network create", keep=r"^(name|id|status|mtu|provider:network_type|router:external|shared)$")}
{T("ex3", r"subnet create")}
{T("ex3", r"network show", keep=r"^(name|id|status|mtu|provider:network_type|subnets|admin_state_up)$")}
{shot("08-networks", "Project networks: student-network with student-subnet 192.168.10.0/24, next to the public and shared networks.", H + "/project/networks/")}
{shot("09-network-detail", "student-network details: Geneve overlay, MTU 1442, active, internal.", H + "/project/networks/<id>/detail")}
{shot("10-subnets", "Subnets tab of student-network: CIDR, IP version and gateway 192.168.10.1.", H + "/project/networks/<id>/detail?tab=subnets")}
{T("ex3", r"subnet show", keep=r"^(name|cidr|gateway_ip|dns_nameservers|allocation_pools|enable_dhcp|ip_version|network_id)$")}
<h3>Interpretation</h3>
<p>The network <code>student-network</code> is <code>ACTIVE</code>, is an internal (not external) network, and
uses a <b>Geneve</b> overlay (OVN), which is why its MTU is 1442 instead of 1500. The subnet
<code>student-subnet</code> is attached to it with CIDR <code>192.168.10.0/24</code>, gateway
<code>192.168.10.1</code>, DNS <code>8.8.8.8</code>, DHCP enabled, and an allocation pool of
<code>192.168.10.2</code> to <code>192.168.10.254</code>.</p>
<ul>
<li><b>Role of Neutron:</b> it creates and manages virtual networks for tenants: L2 networks, IP subnets with
DHCP, routers, NAT and floating IPs, and security groups, all isolated between projects.</li>
<li><b>Network vs subnet:</b> a network is an isolated layer-2 segment (a virtual switch). A subnet is a layer-3
IP address block attached to that network, which defines which addresses ports on the network get. One network
can carry several subnets (our <code>public</code> network has an IPv4 and an IPv6 subnet).</li>
<li><b>Subnet range</b> defines the addresses available to instances. The <b>gateway</b> is the address of the
router interface that instances use to reach other networks. The <b>DNS server</b> is pushed to instances by DHCP
so they can resolve names.</li>
<li>An instance needs a network to get an IP address and a virtual NIC. Without one it cannot communicate with
other instances, the metadata service, or the outside world, and cannot be reached by SSH.</li>
</ul>
""")

# ---------------------------------------------------------------- Exercise 4
S.append(f"""
<h2 class="ex">Exercise 4: Configure a key pair and security group</h2>
<p><b>What I did.</b> I generated an ed25519 key pair on the DevStack VM (with <code>-N ""</code> to skip the
passphrase prompt), registered the public key in Nova as <code>student-key</code>, created the security group
<code>student-security</code> and added the SSH and ICMP rules. Only the public key and fingerprints are shown;
the private key never left the VM.</p>
{T("ex4", r"ssh-keygen")}
{T("ex4", r"keypair create")}
{T("ex4", r"keypair list")}
{T("ex4", r"security group create", keep=r"^(name|id|description|stateful|project_id)$")}
{T("ex4", r"rule create --proto tcp", keep=r"^(direction|ether_type|protocol|port_range_min|port_range_max|remote_ip_prefix|security_group_id)$")}
{T("ex4", r"rule create --proto icmp", keep=r"^(direction|ether_type|protocol|port_range_min|port_range_max|remote_ip_prefix|security_group_id)$")}
{T("ex4", r"rule list")}
{shot("11-keypairs", "Key pairs: student-key (ssh) with its fingerprint. Only the public part is stored in OpenStack.", H + "/project/key_pairs")}
{shot("12-secgroup-rules", "Rules of student-security: default egress rules plus ingress ICMP and TCP 22 (SSH).", H + "/project/security_groups/<id>/")}
<h3>Interpretation</h3>
<ul>
<li><b>SSH key pair:</b> two mathematically linked keys used for passwordless authentication. The <b>public
key</b> can be shared freely; Nova injects it into the instance's <code>authorized_keys</code>. The <b>private
key</b> stays secret on the client and proves our identity during the SSH handshake. Anyone with the private key
can log in, so it must never be shared.</li>
<li><b>Security group:</b> a stateful virtual firewall applied to an instance's ports. By default everything
inbound is denied and everything outbound is allowed, as the two default egress rules (IPv4 and IPv6) show.</li>
<li><b>Allowed traffic:</b> the TCP rule allows inbound SSH on port 22, and the ICMP rule allows inbound ICMP
(for example <code>ping</code>), both from any IPv4 address (<code>0.0.0.0/0</code>). Because the group is
stateful, replies to allowed traffic are permitted automatically.</li>
<li><b>Closing unused ports</b> reduces the attack surface: every open port is a service an attacker can probe or
exploit. Only what is needed should be opened, and ideally from a restricted source range rather than
<code>0.0.0.0/0</code>.</li>
</ul>
""")

# ---------------------------------------------------------------- Exercise 5
S.append(f"""
<h2 class="ex">Exercise 5: Launch a virtual machine</h2>
<p><b>What I did.</b> After checking that all prerequisites exist, I launched <code>student-vm</code> with the
CirrOS image, the <code>m1.tiny</code> flavor, <code>student-network</code>, <code>student-key</code> and
<code>student-security</code>, then followed it until it was <code>ACTIVE</code> and the guest had booted.</p>
{T("ex5", r"keypair list")}
{T("ex5", r"security group list", note="Security groups of all projects are visible because we are admin; ours is student-security.")}
{T("ex5", r"server create", keep=r"^(name|id|status|OS-EXT-STS:vm_state|OS-EXT-STS:task_state|image|key_name|adminPass|security_groups)$")}
{T("ex5", r"server list")}
{T("ex5", r"server show", keep=r"^(name|status|OS-EXT-STS:power_state|OS-EXT-STS:vm_state|OS-EXT-SRV-ATTR:host|OS-EXT-SRV-ATTR:instance_name|image|flavor|addresses|key_name|security_groups|created)$")}
{T("ex5", r"console log")}
{shot("13-instances", "Instances list: student-vm Active and Running, with its fixed and floating IPs, m1.tiny and student-key.", H + "/project/instances/")}
{shot("14-instance-overview", "student-vm overview: host, flavor specs, IP address, security group rules, key pair, image and the attached volume.", H + "/project/instances/<id>/")}
{shot("15-console-log", "student-vm console log in Horizon: network configuration, cloud metadata and the login prompt.", H + "/project/instances/<id>/?tab=log")}
<h3>Interpretation</h3>
<p>The instance went from <code>BUILD</code> (vm_state <i>building</i>, task_state <i>scheduling</i>) to
<code>ACTIVE</code> with power state <i>Running</i> on host <code>ip-172-31-19-63</code>.</p>
<table class="grid">
<tr><th>Status</th><td>ACTIVE</td></tr>
<tr><th>Image</th><td>cirros-0.6.3-x86_64-disk</td></tr>
<tr><th>Flavor</th><td>m1.tiny (1 vCPU, 512 MB RAM, 1 GB disk)</td></tr>
<tr><th>Network</th><td>student-network</td></tr>
<tr><th>Fixed IP</th><td>192.168.10.112</td></tr>
</table>
<p>The console log confirms the guest really booted: <code>dhcpcd</code> obtained the lease
<code>192.168.10.112</code> from <code>192.168.10.1</code>, the root filesystem was resized to the flavor's disk,
the SSH server (<code>dropbear</code>) started, and the login prompt <code>student-vm login:</code> appeared.</p>
<ul>
<li><b>Instance:</b> a running virtual machine created from an image and sized by a flavor, attached to one or
more networks and managed by Nova.</li>
<li><b>Role of Nova:</b> nova-api receives the request and checks it against Keystone; nova-scheduler, with
Placement, picks a host that has enough resources for the flavor; nova-conductor coordinates the build;
nova-compute on that host downloads the image from Glance, asks Neutron for a port and IP, asks Cinder for volumes
if needed, and starts the VM through libvirt/QEMU.</li>
<li><b>ACTIVE</b> means the build finished and the hypervisor reports the VM as running. It does not guarantee the
guest OS finished booting or is reachable on the network.</li>
<li><b>Reasons for not reaching ACTIVE (status ERROR or stuck in BUILD):</b> (1) no host has enough free resources
for the flavor ("No valid host was found"), for example choosing <code>m1.xlarge</code> on our 8 GB host;
(2) Neutron fails to create or bind the port (network agent down, wrong network name); other causes are a corrupt
or incompatible image, or the nova-compute service being down.</li>
</ul>
""")

# ---------------------------------------------------------------- Exercise 6
S.append(f"""
<h2 class="ex">Exercise 6: Test connectivity and floating IP</h2>
<p><b>What I did.</b> The fixed IP of <code>student-vm</code> is <code>192.168.10.112</code>. Our environment has
an external provider network <code>public</code> (<code>172.24.4.0/24</code>) and a router <code>router1</code>
with a gateway on it, so the conditional part was attempted.</p>
{T("ex6", r"server show student-vm -c addresses$")}
{T("ex6", r"floating ip list", note="No floating IP existed before the test.")}
{T("ex6", r"network list --external")}
{T("ex6", r"floating ip create", keep=r"^(floating_ip_address|floating_network_id|fixed_ip_address|status|id)$")}
<p>A floating IP is only reachable if the instance's subnet is connected to a router that has a gateway on the
external network. <code>router1</code> was only connected to the default private subnet, so I attached
<code>student-subnet</code> to it before associating the floating IP.</p>
{T("ex6", r"router show")}
{T("ex6", r"router add subnet")}
{T("ex6", r"server add floating ip")}
{T("ex6", r"server show student-vm -c addresses -c status")}
{T("ex6", r"floating ip list", nth=1)}
<h3>First test: ACTIVE but unreachable</h3>
<p>The floating IP was associated correctly, but ping and SSH failed:</p>
{T("ex6", r"^ping")}
{T("ex6", r"^ssh")}
<p><b>Diagnosis.</b> In DevStack, the host reaches the <code>public</code> network through the OVS bridge
<code>br-ex</code>, which DevStack configures with the address <code>172.24.4.1/24</code>. That address is not
persistent: our host had been stopped and restarted since <code>stack.sh</code> ran, so <code>br-ex</code> had no IP
and the host had no route to <code>172.24.4.0/24</code>. This was a host network configuration problem, not an
OpenStack or security group problem. I restored the address and tested again:</p>
{T("ex6b", r"ip -4 addr show br-ex", 0)}
{T("ex6b", r"ip addr add")}
{T("ex6b", r"ip -4 addr show br-ex", 1)}
{T("ex6b", r"ip route")}
{T("ex6b", r"^ping")}
{T("ex6b", r"^ssh")}
{shot("16-floating-ips", "Floating IPs: an address from the public pool mapped to the fixed IP of student-vm.", H + "/project/floating_ips/")}
{shot("17-topology", "Network topology of the admin project: student-vm attached to student-network. router1 belongs to the demo project, so Horizon does not draw it in this project's view.", H + "/project/network_topology/")}
<h3>Interpretation</h3>
<p>After the fix, the floating IP <code>172.24.4.2</code> answers ping with 0% loss and SSH works with the
<code>cirros</code> user and our private key, with no password. Inside the instance, <code>eth0</code> only has the
fixed IP <code>192.168.10.112</code>: the floating IP is never configured in the guest, it exists only as a NAT
rule on the router. From inside, the instance also reaches its gateway <code>192.168.10.1</code>.</p>
<p><b>How to test the fixed IP.</b> The fixed IP is only reachable from the same tenant network or through the
router. Valid methods are: from another instance on <code>student-network</code>, run
<code>ping 192.168.10.112</code> and <code>ssh cirros@192.168.10.112</code>; or from the DevStack host, use the
OVN metadata namespace (<code>sudo ip netns exec ovnmeta-&lt;network-id&gt; ping 192.168.10.112</code>), which is
attached to that network. Pinging the fixed IP from our laptop would not work, because it is a private overlay
address.</p>
<ul>
<li><b>Fixed vs floating IP:</b> a fixed IP is the private address assigned to the instance's port by DHCP on its
tenant subnet; it stays for the life of the port. A floating IP is a public address from the external network
pool, mapped to the fixed IP by 1:1 NAT on the router. It can be detached and moved to another instance.</li>
<li><b>ACTIVE but no SSH:</b> the guest may still be booting; the security group may not allow port 22 or ICMP;
the subnet may not be attached to a router with an external gateway; the wrong user or key may be used; or, as we
saw, the host may have no route to the external network.</li>
<li><b>Floating IP unavailable in DevStack:</b> a local installation may have no external provider network or
router gateway, the <code>public</code> network may be fake (only reachable from the host itself, as here:
<code>172.24.4.0/24</code> is not routable from the Internet), the pool may be exhausted, or the bridge may be
misconfigured after a reboot.</li>
<li><b>Roles in connectivity:</b> the network configuration (subnet, router, gateway, NAT) decides whether a
packet has a <i>path</i> to the instance. The security group decides whether the packet is <i>allowed</i> once it
arrives. Both must be correct: with the right path but no SSH rule, the connection is dropped; with the rule but
no router, no packet ever arrives.</li>
</ul>
""")

# ---------------------------------------------------------------- Exercise 7
S.append(f"""
<h2 class="ex">Exercise 7: Explore block storage and snapshots</h2>
<p><b>What I did.</b> Cinder is installed and working (scheduler and volume service are up, with the LVM backend
<code>lvmdriver-1</code>), so I created a 1 GB volume, attached it to <code>student-vm</code>, checked it from inside
the instance, and created an instance snapshot.</p>
{T("ex7", r"volume service list")}
{T("ex7", r"volume type list")}
{T("ex7", r"volume list", note="No volumes existed before the test.")}
{T("ex7", r"volume create", keep=r"^(name|id|size|status|type|bootable|attachments)$")}
{T("ex7", r"volume show student-volume$", keep=r"^(name|id|size|status|type|bootable|attachments)$")}
{T("ex7", r"server add volume")}
{T("ex7", r"volume show student-volume -c")}
{T("ex7b", r"^ssh")}
{T("ex7", r"server image create", keep=r"^(name|id|status|disk_format|container_format|size|virtual_size|visibility)$")}
{T("ex7", r"image list")}
{shot("05-volume-services", "Block Storage services: cinder-scheduler and cinder-volume (lvmdriver-1) up.", H + "/admin/info/?tab=system_info__cinder_services")}
{shot("19-volume-types", "Volume types: lvmdriver-1 (LVM backend) and __DEFAULT__.", H + "/admin/volume_types/")}
{shot("18-volumes", "Volumes: student-volume, 1 GiB, In-use, attached to student-vm on /dev/vdb.", H + "/project/volumes/")}
{shot("06-images", "Images: the CirrOS image and our instance snapshot student-vm-snapshot (type Snapshot, private, QCOW2).", H + "/project/images")}
<h3>Interpretation</h3>
<p>The volume went from <code>creating</code> to <code>available</code>, then to <code>in-use</code> after the
attach. Inside the guest, <code>lsblk</code> shows a new 1 GB disk <code>vdb</code> next to the 1 GB root disk
<code>vda</code>, and the kernel log shows the virtio disk being hot-plugged. The snapshot
<code>student-vm-snapshot</code> is a new <code>active</code> qcow2 image in Glance (about 51 MB) and appears in the
image list next to CirrOS. (The initial in-guest check failed with a timeout for the same <code>br-ex</code> reason
as in Exercise 6; the output above is after the fix.)</p>
<ul>
<li><b>Role of Cinder:</b> it provides persistent block storage. It creates volumes on a backend (here LVM on the
host), and attaches and detaches them to instances, where they appear as ordinary disks. It also offers volume
snapshots and backups.</li>
<li><b>Root disk vs volume:</b> the root disk is ephemeral: it is created from the image when the instance is
built and is destroyed when the instance is deleted. A Cinder volume has its own lifecycle: it survives instance
deletion and can be detached and attached to another instance.</li>
<li><b>Instance snapshot:</b> a copy of the instance's root disk at a point in time, stored in Glance as a new
image. It is useful as a backup before risky changes, to clone a configured server into several identical
instances, or to rebuild an instance after a failure.</li>
<li><b>If Cinder were not configured:</b> the <code>volume</code> commands would fail (no block-storage endpoint in
the catalog), so the environment could only use ephemeral storage. Data would then be lost when the instance is
deleted. In our environment this does not apply, since Cinder is available.</li>
</ul>
""")

# ---------------------------------------------------------------- Exercise 8
S.append(f"""
<h2 class="ex">Exercise 8: Resource lifecycle and cleanup</h2>
<p><b>What I did.</b> I displayed the instance status, stopped it to show the difference with deletion, then
deleted every resource I created, in dependency order.</p>
{T("ex8", r"server show student-vm -c name -c status", 0)}
{T("ex8", r"server stop")}
{T("ex8", r"server show student-vm -c name -c status", 1)}
<p><b>Stop vs delete.</b> Stopping (<code>SHUTOFF</code>) powers the VM off but keeps it: its root disk, fixed IP,
port, attached volumes and the resources reserved for its flavor stay allocated, and it can be started again.
Deleting destroys the instance and its ephemeral root disk and frees its port, IP and resources. Only separate
objects such as Cinder volumes, snapshots and floating IPs survive deletion.</p>
<p><b>Resources created in this assignment:</b></p>
<table class="grid">
<tr><th>Instance</th><td>student-vm</td></tr>
<tr><th>Snapshot</th><td>student-vm-snapshot (Glance image)</td></tr>
<tr><th>Volume</th><td>student-volume</td></tr>
<tr><th>Floating IP</th><td>172.24.4.2</td></tr>
<tr><th>Router interface</th><td>student-subnet on router1 (router1 itself is pre-existing)</td></tr>
<tr><th>Key pair</th><td>student-key</td></tr>
<tr><th>Security group</th><td>student-security</td></tr>
<tr><th>Network / subnet</th><td>student-network / student-subnet</td></tr>
<tr><th>Flavor</th><td>student.small</td></tr>
</table>
<p>Cleanup order: detach the volume before deleting it, release the floating IP, delete the instance (which frees
its port), remove the router interface, then delete the subnet and network, and finally the security group, key
pair and flavor. Pre-existing resources (<code>router1</code>, the <code>public</code>, <code>private</code> and
<code>shared</code> networks, the CirrOS image and the default flavors) were not touched.</p>
{T("ex8", r"remove volume")}
{T("ex8", r"remove floating ip")}
{T("ex8", r"floating ip delete")}
{T("ex8", r"server delete")}
{T("ex8", r"volume delete")}
{T("ex8", r"image delete")}
{T("ex8", r"router remove subnet")}
{T("ex8", r"subnet delete")}
{T("ex8", r"network delete")}
{T("ex8", r"security group delete")}
{T("ex8", r"keypair delete")}
{T("ex8", r"flavor delete")}
<p><b>Verification.</b> Every delete command returned without error. The final listings show no instance, volume,
key pair or floating IP, and only the pre-existing image and networks:</p>
{T("ex8", r"server list")}
{T("ex8", r"volume list")}
{T("ex8", r"image list")}
{T("ex8", r"network list")}
{T("ex8", r"keypair list")}
{T("ex8", r"floating ip list")}

<h2>Conclusion</h2>
<p>This assignment covered the full IaaS workflow on our own OpenStack: Keystone authenticated every request,
Glance supplied the image, Neutron built an isolated network with DHCP, routing and NAT, Nova scheduled and
booted the instance, security groups and key pairs controlled access, and Cinder added persistent storage. All
exercises, including the conditional floating IP and block storage parts, succeeded in this environment. The
main lesson from the one failure was that an <code>ACTIVE</code> instance is not necessarily reachable: the
floating IP only worked once the host's external bridge <code>br-ex</code> had its address back after a reboot.</p>
""")

CSS = """
@page { size: A4; margin: 16mm 14mm; }
:root { --ink:#1d2330; --muted:#5b6475; --line:#d9dee7; --accent:#c8102e; --term:#14181f; }
body { font: 10.5pt/1.5 "Helvetica Neue", Helvetica, Arial, sans-serif; color: var(--ink); background: #fff; }
h1 { font-size: 17pt; line-height: 1.25; margin: 3mm 0 2mm; }
h2 { font-size: 14pt; margin: 9mm 0 3mm; padding-bottom: 1.5mm; border-bottom: 2px solid var(--accent); break-after: avoid; }
h3 { font-size: 11pt; margin: 5mm 0 2mm; break-after: avoid; }
p, li { text-align: justify; }
ul { padding-left: 5mm; } li { margin-bottom: 1.5mm; }
code { font: 9pt "SF Mono", Menlo, Consolas, monospace; background: #f1f3f7; padding: 0 3px; border-radius: 3px; }
.cover { border-bottom: 1px solid var(--line); padding-bottom: 4mm; }
.school { color: var(--muted); font-size: 10pt; }
.who { font-size: 11pt; font-weight: 600; }
table.meta th { text-align: left; padding: 3mm 8mm 3mm 0; color: var(--muted); font-weight: 600; }
table.grid { border-collapse: collapse; margin: 2mm 0 3mm; font-size: 9.5pt; }
table.grid th, table.grid td { border: 1px solid var(--line); padding: 1.3mm 3mm; text-align: left; vertical-align: top; }
table.grid th { background: #f5f6f9; width: 38mm; }
figure.term { margin: 2.5mm 0 3.5mm; border-radius: 6px; overflow: hidden; background: var(--term); break-inside: avoid; }
.bar { background: #2a303b; padding: 1.4mm 3mm; display: flex; align-items: center; gap: 1.4mm; }
.bar i { width: 2.4mm; height: 2.4mm; border-radius: 50%; background: #ff5f57; display: inline-block; }
.bar i:nth-child(2) { background: #febc2e; } .bar i:nth-child(3) { background: #28c840; }
.bar span { color: #aab2c0; font: 7.5pt Menlo, monospace; margin-left: 2mm; }
figure.term pre { margin: 0; padding: 2.5mm 3mm; color: #d7dce4; font: 6.6pt/1.35 "SF Mono", Menlo, Consolas, monospace; white-space: pre; overflow: hidden; }
.p { color: #6fd08c; font-weight: 700; } .c { color: #ffffff; font-weight: 700; } .dim { color: #7d8594; font-style: italic; }
figure.shot { margin: 3mm 0 5mm; border: 1px solid #cfd5df; border-radius: 7px; overflow: hidden; break-inside: avoid; box-shadow: 0 1px 4px rgba(20,24,31,.12); }
figure.shot img { display: block; width: 100%; }
.url { background: #eceff3; border-bottom: 1px solid #d6dbe3; padding: 1.4mm 3mm; display: flex; align-items: center; gap: 1.4mm; }
.url i { width: 2.4mm; height: 2.4mm; border-radius: 50%; background: #ff5f57; display: inline-block; }
.url i:nth-child(2) { background: #febc2e; } .url i:nth-child(3) { background: #28c840; }
.url span { margin-left: 3mm; background: #fff; border: 1px solid #d6dbe3; border-radius: 10px; padding: .4mm 3mm; font: 7.5pt Menlo, monospace; color: #3d4452; flex: 1; }
figure.shot figcaption, figure.diagram figcaption { font-size: 8.5pt; color: #5b6475; padding: 1.8mm 3mm; background: #fafbfc; border-top: 1px solid #e3e7ee; }
figure.diagram { margin: 3mm 0 5mm; border: 1px solid #e3e7ee; border-radius: 7px; overflow: hidden; break-inside: avoid; }
figure.diagram svg { display: block; width: 100%; padding: 2mm; box-sizing: border-box; }
.toc { margin-top: 16mm; } .toc h3 { color: var(--muted); } .toc ol { font-size: 11pt; line-height: 1.9; } .toc li::marker { color: var(--accent); font-weight: 700; }
h2.ex { break-before: page; }
.cap { background: #1f242d; color: #9aa3b2; font-size: 7.5pt; padding: 1.2mm 3mm; font-style: italic; }
"""

OUT.write_text(f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<title>TP4 OpenStack Report</title><style>{CSS}</style></head><body>{''.join(S)}</body></html>""")
print("wrote", OUT)
