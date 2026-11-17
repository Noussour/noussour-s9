// Logs into Horizon and captures screenshots of the pages used in the TP4 report.
// Usage: HZ_PW=... SG_ID=... VM_ID=... NET_ID=... node shoot.mjs <base-url> <out-dir>
import puppeteer from "puppeteer-core";

const [base, out] = process.argv.slice(2);
const { HZ_PW, SG_ID, VM_ID, NET_ID } = process.env;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

const browser = await puppeteer.launch({
  executablePath: process.env.HOME + "/Library/Caches/ms-playwright/chromium-1228/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing",
  headless: true,
  args: ["--no-first-run", "--no-proxy-server"],
  defaultViewport: { width: 1440, height: 900, deviceScaleFactor: 2 },
});
const page = await browser.newPage();

async function shot(name, path, { wait = 1500, full = false, clip = null, before = null } = {}) {
  await page.goto(base + path, { waitUntil: "networkidle2", timeout: 60000 });
  if (before) await before();
  await sleep(wait);
  const opts = { path: `${out}/${name}.png`, fullPage: full };
  if (clip) opts.clip = clip;
  await page.screenshot(opts);
  console.log("shot", name);
}

// login page (before signing in)
await shot("00-login", "/dashboard/auth/login/", { wait: 800 });

await page.type("#id_username", "admin");
await page.type("#id_password", HZ_PW);
await Promise.all([page.waitForNavigation({ waitUntil: "networkidle2" }), page.click("#loginBtn")]);

// resources live in the admin project; Horizon defaults to demo
await page.goto(base + "/dashboard/auth/switch/d62cc16c9a514011b1a706dfa0b5e7d5/?next=/dashboard/project/", { waitUntil: "networkidle2" });

const pages = [
  ["01-overview", "/dashboard/project/", { wait: 2500 }],
  ["02-services", "/dashboard/admin/info/"],
  ["03-compute-services", "/dashboard/admin/info/?tab=system_info__nova_services"],
  ["04-network-agents", "/dashboard/admin/info/?tab=system_info__network_agents"],
  ["05-volume-services", "/dashboard/admin/info/?tab=system_info__cinder_services"],
  ["06-images", "/dashboard/project/images"],
  ["07-flavors", "/dashboard/admin/flavors/"],
  ["08-networks", "/dashboard/project/networks/"],
  ["09-network-detail", `/dashboard/project/networks/${NET_ID}/detail`],
  ["10-subnets", `/dashboard/project/networks/${NET_ID}/detail?tab=network_tabs__subnets_tab`],
  ["11-keypairs", "/dashboard/project/key_pairs"],
  ["12-secgroup-rules", `/dashboard/project/security_groups/${SG_ID}/`],
  ["13-instances", "/dashboard/project/instances/"],
  ["14-instance-overview", `/dashboard/project/instances/${VM_ID}/`, { full: true }],
  ["15-console-log", `/dashboard/project/instances/${VM_ID}/?tab=instance_details__log`, { wait: 4000 }],
  ["16-floating-ips", "/dashboard/project/floating_ips/"],
  ["17-topology", "/dashboard/project/network_topology/", { wait: 6000 }],
  ["18-volumes", "/dashboard/project/volumes/"],
  ["19-volume-types", "/dashboard/admin/volume_types/"],
];
for (const [n, p, o] of pages) {
  try { await shot(n, p, o || {}); } catch (e) { console.log("FAIL", n, e.message); }
}
await browser.close();
