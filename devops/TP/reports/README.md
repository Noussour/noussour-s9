# DevOps lab reports

The revised **GitHub Codespaces report uses the user's real execution screenshots**. The separate original VMware/Azure reports are worked solutions and reproducible procedures with explicitly simulated illustrations. No Azure resources were created to produce these reports.

- `TP2-Codespaces-report.pdf` / `TP2-Codespaces-report.md`: completed report for `TP2_Lab Cloud Environment Pr.pdf`, using nine genuine screenshots, observed results and all nine answers. The missing account-usage screenshot and unshown port-visibility setting are identified explicitly.
- `evidence/`: unchanged original clipboard bitmaps, lossless PNG convenience copies, and their provenance/hash manifest. No image content was edited.

- `TP1-report.pdf` / `TP1-report.md`: all eleven TP1 questions, the original VMware/Linux Lite procedure, and an Azure CLI adaptation with its limitations.
- `TP2-report.pdf` / `TP2-report.md`: Azure provisioning, restricted SSH/HTTP, Nginx, every question, cost estimation, troubleshooting, and cleanup.
- `TP2-short-report.pdf` / `TP2-short-report.md`: concise answers matching the lab's short-report requirement.
- `assets/`: simulated terminal/browser illustrations and their editable JSON source.
- `scripts/`: Bash procedures intended for WSL/Linux with Azure CLI and OpenSSH. Read them before execution; they create billable resources. Cleanup is a separate command.
- `build_reports.py`: rebuild the PDF reports and illustrations with Python, ReportLab, and Pillow. Uses local Windows fonts when available.

## Read and reproduce

Use the sheets alongside the corresponding report: `../Lab1.pdf`, `../TP1-supportpdf.pdf`, `../TP2_Lab Cloud Environment.pdf` (Azure option), and `../TP2_Lab Cloud Environment Pr.pdf` (revised GitHub Codespaces option).

For Azure, start in WSL/Linux on your own computer, run `az login`, choose your subscription, and check regional availability and your budget. Set `CLIENT_IP` to the public IPv4 address of the computer that will make the SSH/browser connections. Cloud Shell's public IP may differ from your browser's egress IP.

```bash
export CLIENT_IP="YOUR_REAL_PUBLIC_IPV4"
export LOCATION="francecentral"
export ADMIN="azureuser"  # use your own surname if required
bash scripts/tp2-azure.sh
# Or, in a different resource group:
bash scripts/tp1-azure.sh
```

The scripts do not execute Nginx installation or snapshot experiments automatically. They print the next commands so you can collect actual observations. Follow each report in order. Set `RG` to the lab group when using `scripts/cleanup.sh`.

```bash
export RG="rg-devops-tp2"
bash scripts/cleanup.sh
```

The cleanup script only accepts the two fixed lab group names and checks the `purpose=devops-lab` tag. Never place unrelated resources in those groups. It deletes the whole selected group after requiring you to type its name.

## Rebuild locally

```bash
python -m pip install reportlab pillow
python build_reports.py
```

The PDFs contain source links checked on 3 November 2026. Prices, image versions, SKU availability, quotas and policy vary. The Codespaces report records only results visible in the supplied captures. Azure subscription charges, boot measurements and deployment health were not inspected.

Use the Markdown and shell files when copying commands: long commands are visually wrapped in the PDFs.

If Windows locks an existing standalone PNG, the builder preserves that file and still embeds the newly rendered figure directly in the PDF. Close any image preview and rebuild to refresh the standalone file.
