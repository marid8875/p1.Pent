# Pentest Suite

A single PyQt5 GUI that wraps the most common Linux pentesting tools
(already installed on Kali Linux) into one click-only interface — no
manual command typing required.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/platform-Linux-informational)
![License](https://img.shields.io/badge/license-MIT-green)

## ⚠️ Legal Disclaimer

This tool is for **authorized security testing and education only**.
Only run it against systems you own or have explicit written permission
to test. Unauthorized access to computer systems is illegal in most
jurisdictions. The authors take no responsibility for misuse.

## Features

- 19 tools across 5 categories: Reconnaissance, Vulnerability Scanning,
  Password Cracking, Wireless, Post-Exploitation
- Live, streaming command output (no waiting for the tool to finish)
- Pre-flight checks: warns if a required wordlist is missing, if the
  underlying binary isn't installed, or if a tool likely needs root
- Interactive tools (e.g. Metasploit) are launched in their own terminal
  window instead of being force-fit into the output panel
- Save session output to a text file
- Adding a new tool requires editing only `tools_config.py` — no GUI code
  changes needed

## Requirements

- Linux (tested on Kali Linux; any Debian-based distro works)
- Python 3.8+
- The underlying CLI tools you intend to use (nmap, nikto, hydra, sqlmap,
  gobuster, wpscan, john, aircrack-ng suite, netcat, metasploit-framework,
  theharvester, whois, dnsutils). Most of these ship by default on Kali.

## Installation

```bash
git clone https://github.com/<your-username>/pentest-suite.git
cd pentest-suite
pip install -r requirements.txt --break-system-packages
```

If a tool you plan to use isn't installed yet (non-Kali distros):

```bash
sudo apt update
sudo apt install nmap nikto dirb gobuster wpscan sqlmap hydra john \
    aircrack-ng netcat-traditional theharvester whois dnsutils \
    metasploit-framework -y
```

## Usage

```bash
python3 main.py
```

1. Enter the target (IP, domain, or URL depending on the tool).
2. Fill in the wordlist field if the selected tool needs one (a file
   path for most tools, a port number for the Netcat listener).
3. Click a tool in the tabs to see its description and the exact command
   that will run.
4. Click **Run**. You'll get a confirmation prompt, then live output.
5. Stop, clear, or save the output at any time.

## Project Structure

```
pentest-suite/
├── main.py            # GUI + execution logic (PyQt5 + QProcess)
├── tools_config.py     # Tool definitions (name, description, command template)
├── requirements.txt    # Python dependencies
├── LICENSE
└── README.md
```

## Adding a New Tool

Open `tools_config.py` and add an entry to the relevant category:

```python
{
    "name": "My Tool",
    "desc": "What it does.",
    "cmd": "mytool -x {target}",
    "requires_wordlist": False,  # optional
    "requires_root": False,      # optional
},
```

No changes to `main.py` are needed.

## Known Limitations

- **Wireless tools** (Airmon-ng, Airodump-ng) require a USB Wi-Fi adapter
  that supports monitor mode; most built-in laptop cards and virtual
  machines do not support this.
- **WPScan** needs a free API token from wpscan.com for full
  vulnerability data; without it, results are limited.
- **Hydra - Web Login Form** uses a generic template (`/login`,
  `user`/`pass` fields) that will need manual editing to match the
  real target's form.
- Tools marked as interactive (e.g. Metasploit) open in a separate
  terminal window and are not captured in the app's output panel.

## License

MIT — see [LICENSE](LICENSE).
