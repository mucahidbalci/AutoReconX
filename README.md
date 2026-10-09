# 🔥 AutoReconX ULTRA PRO

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8+-blue.svg?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/Nmap-Scanning-003366?logo=linux" alt="Nmap">
  <img src="https://img.shields.io/badge/TR--CERT-Integrated-red.svg" alt="TR-CERT">
  <img src="https://img.shields.io/github/stars/mucahidbalci/AutoReconX?style=social" alt="Stars">
</p>

<h3 align="center">The Most Powerful Ethical Cybersecurity Platform for Full System Vulnerability Scanning</h3>

<p align="center">
  XSS · SQLi · LFI · CVE · SSL · Cloud · DNS · Web Vulnerabilities & much more<br>
  KVKK Compliant · TR-CERT Integrated · TÜBİTAK SGE Standards
</p>

<p align="center">
  ⭐ <strong>If this project helps you, please give it a star!</strong> It motivates me to build more.
</p>

---

## 🚀 What is AutoReconX?

**AutoReconX ULTRA PRO** is an enterprise-grade, ethical cybersecurity reconnaissance platform built for **penetration testers, security researchers, and blue teams**. It combines multiple security modules into a single, intelligent scanning engine that produces professional HTML/JSON reports compliant with Turkish (KVKK) and international (PTES/OSSTMM) standards.

> Built by a young cybersecurity researcher to make professional-grade security assessment accessible, ethical, and actionable.

---

## ✨ Key Features

### 🔍 Comprehensive Vulnerability Scanning
- **Port Scanning** — Nmap integration with service version detection, CVE correlation, and exploit suggestions
- **Web Application Testing** — XSS, SQL Injection, LFI, open directories, exposed admin panels, API documentation leaks
- **SSL/TLS Deep Analysis** — Heartbleed, POODLE, weak ciphers, certificate issues via `testssl.sh`
- **DNS Intelligence** — Subdomain enumeration (Amass), zone transfer attempts, DNSSEC analysis
- **Cloud Asset Discovery** — AWS S3 bucket hunting with Turkish-sensitive naming patterns
- **Threat Intelligence** — AbuseIPDB reputation, VirusTotal domain scoring, TR-CERT ransomware list check

### 🛡️ TR-CERT Integration
Real-time integration with **TR-CERT (Turkish Computer Emergency Response Team)** ransomware database. Automatically flags domains listed in the national ransomware watchlist.

### 📊 Professional Reporting
- **HTML Reports** — Beautiful, responsive, executive-summary-ready reports with color-coded severity cards
- **JSON Exports** — Machine-readable findings for SIEM/SOAR integration
- **CVSS Scoring** — Standardized risk scoring with remediation timelines
- **KVKK Compliance** — Built-in data protection warnings and consent workflows

### 🎯 TÜBİTAK SGE Standards
Aligned with Turkey's National Cyber Security Exercise standards for professional pentest reporting.

### ⚡ Intelligent Automation
- **Adaptive Scanning Intensity** — Stealth / Balanced / Aggressive / Full modes
- **Concurrent Module Execution** — Async architecture with configurable timeouts
- **System Health Monitoring** — CPU, memory, disk, and network status checks before scanning
- **Graceful Shutdown** — Safe `Ctrl+C` handling without corrupting reports

### 🔐 Ethical-First Design
- Mandatory legal disclaimer acceptance
- KVKK (Turkish GDPR) consent workflow
- Security code verification before each scan
- Institutional authorization tracking (organization name, permit number, authorized person)

---

## 📦 Installation

### Prerequisites
- **Python 3.8+**
- **Kali Linux / Debian-based OS** (recommended)
- System-level tools: `nmap`, `testssl.sh`, `whatweb`, `nikto`, `dirsearch`, `amass`

### Step 1: Install System Dependencies

```bash
sudo apt update
sudo apt install -y python3-pip nmap testssl.sh whatweb nikto dirsearch amass
```

### Step 2: Clone the Repository

```bash
git clone https://github.com/mucahidbalci/AutoReconX.git
cd AutoReconX
```

### Step 3: Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

> **Note:** `requirements.txt` includes: `rich`, `aiohttp`, `dnspython`, `python-whois`, `tldextract`, `jinja2`, `aiofiles`, `psutil`

---

## 💻 Usage

Run the tool from your terminal:

```bash
python3 AutoReconX.py
```

### Interactive Workflow

1. **System Health Check** — Verifies CPU, memory, disk, and network status
2. **Legal & Ethical Compliance** — Accept KVKK terms + enter security code
3. **Institutional Information** — Organization name, permit number, authorized person
4. **Target Selection** — Domain or IP address
5. **Scan Configuration** — Intensity level (stealth / balanced / aggressive / full)
6. **Module Selection** — Enable/disable specific reconnaissance modules
7. **Optional API Keys** — AbuseIPDB, VirusTotal for enhanced intelligence
8. **Automated Scan** — All enabled modules run in sequence
9. **Report Generation** — HTML + JSON reports saved to output directory

### Example Output Structure

```
otoreconx_1699999999/
├── rapor_1699999999.html      # Professional HTML report
├── bulgular_1699999999.json   # Machine-readable findings
└── konsol.log                 # Full terminal output log
```

---

## 🧩 Available Modules

| Module | Description | Default |
|--------|-------------|---------|
| **Port Scanner** | Nmap with version detection + CVE correlation | ✅ |
| **DNS Intelligence** | Subdomain enumeration, zone transfer, DNSSEC | ✅ |
| **SSL Analyzer** | `testssl.sh` deep TLS analysis | ✅ |
| **Web Analyzer** | Tech fingerprinting, security headers, vuln scan | ✅ |
| **Cloud Hunter** | S3 bucket discovery (Turkish naming patterns) | ✅ |
| **Threat Intel** | AbuseIPDB + VirusTotal reputation checks | ❌ |
| **Misconfiguration** | Default credentials, open directories | ✅ |
| **TR-CERT Check** | National ransomware watchlist | ✅ |

---

## 🎯 Scan Intensity Modes

| Mode | Timeout | Concurrent Requests | Use Case |
|------|---------|---------------------|----------|
| **Stealth** | 300s | 5 | Covert assessment, avoid IDS triggers |
| **Balanced** | 180s | 20 | Standard professional pentest |
| **Aggressive** | 120s | 40 | Time-constrained engagements |
| **Full** | 60s | 80 | CTF / lab environment only |

---

## 🔑 API Integration (Optional)

For enhanced threat intelligence, you can provide API keys for:

- **AbuseIPDB** — IP reputation scoring (requires free API key)
- **VirusTotal** — Domain reputation and malware detection

Keys are requested interactively and never stored on disk.

---

## 📸 Sample Reports

The tool generates beautiful, executive-ready HTML reports with:

- Severity distribution cards (Critical / High / Medium / Low)
- Color-coded finding cards with CVSS vectors
- Remediation guidance and institutional responsibility assignment
- KVKK compliance footer
- Responsive design for mobile and desktop

---

## ⚠️ Legal & Ethical Disclaimer

This tool is developed strictly for **educational purposes, authorized penetration testing, and legal security research**.

### 🚫 DO NOT use this tool to:
- Scan systems you do not own or have written permission to test
- Target critical infrastructure (hospitals, energy, government) without authorization
- Violate Turkish Law No. 5651 (Internet Crimes) or Law No. 5237 (Turkish Penal Code)
- Harvest personal data without KVKK compliance

### ✅ DO use this tool to:
- Perform authorized red team / pentest engagements
- Conduct academic cybersecurity research
- Learn about vulnerability assessment methodologies
- Build defensive capabilities for your organization

### ⚖️ Legal Framework Compliance
- **Law No. 5651** — Crimes Committed Through Internet
- **Law No. 5237** — Turkish Penal Code
- **Law No. 6698** — Personal Data Protection (KVKK)
- **TÜBİTAK SGE** — National Cyber Security Exercise Standards

> **The developer (Mücahid Balcı) assumes no liability for any misuse or damage caused by this program. Users assume full responsibility for their actions.**

---

## 🛠️ Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Core Language** | Python 3.8+ | Async-first architecture |
| **Network Scanning** | Nmap | Port & service discovery |
| **SSL/TLS Analysis** | testssl.sh | Deep TLS configuration checks |
| **Web Fingerprinting** | whatweb | Technology stack detection |
| **Directory Bruteforce** | dirsearch | Hidden path discovery |
| **Subdomain Enumeration** | amass | DNS reconnaissance |
| **Web Framework** | aiohttp | Async HTTP requests |
| **DNS Resolution** | dnspython | Record enumeration |
| **HTML Reports** | Jinja2 | Templated report generation |
| **Terminal UI** | Rich | Beautiful CLI output |
| **System Monitoring** | psutil | Resource health checks |

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork** the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m 'Add amazing feature'`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a **Pull Request**

### 🧪 Testing Guidelines
- Test on isolated lab environments only
- Include both positive and negative test cases
- Document any new modules with usage examples

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

```
MIT License — roottechx (Mücahid BALCI) — 2025
```

---

## 👤 About the Developer

**Mücahid Balcı** — *Young Entrepreneur & Cybersecurity Researcher*

- 🌐 **Portfolio:** [mucahidbalci.github.io](https://mucahidbalci.github.io)
- 💻 **GitHub:** [@mucahidbalci](https://github.com/mucahidbalci)
- 📧 **Contact:** balcimucahid4@gmail.com

### 🚀 My Other Projects

- **[PyScanPro](https://github.com/mucahidbalci/PyScanPro)** — 150-thread multithreaded port scanner with modern CustomTkinter GUI
- **[PyWebClone](https://github.com/mucahidbalci/PyWebClone)** — Enterprise-grade web cloning & OSINT forensics tool with Playwright

---

## 🙏 Acknowledgments

- **TR-CERT (USOM)** — For maintaining the national ransomware watchlist API
- **TÜBİTAK BİLGEM** — For cybersecurity research standards
- **CVE Program** — For vulnerability database
- **AbuseIPDB & VirusTotal** — For threat intelligence APIs
- The open-source cybersecurity community for continuous inspiration

---

<p align="center">
  <strong>Built with ❤️ for the ethical cybersecurity community</strong><br>
  <sub>🇹🇷 Proudly developed in Türkiye</sub><br>
  <sub>© 2026 Mücahid Balcı. All rights reserved.</sub>
</p>

<p align="center">
  <em>"The stronger you are, the heavier your responsibility becomes."</em>
</p>
