# -*- coding: utf-8 -*-
"""
Tool definitions for Pentest Suite.

Each tool is a dict with:
    name              -> display name
    desc              -> short description shown in the GUI
    cmd               -> command template. Supported placeholders:
                         {target}   the target field
                         {wordlist} the wordlist / extra-value field
    requires_wordlist -> bool, True if the wordlist field is mandatory
    requires_root     -> bool, True if the tool typically needs root/sudo
    external_terminal -> bool, True if the tool is fully interactive and
                         must be launched in its own terminal window
                         instead of being piped into the app's output box
    note              -> optional extra warning/instructions shown before run
"""

TOOLS = {

    "Reconnaissance": [
        {
            "name": "Nmap - Quick Scan",
            "desc": "Scan the most common ports only (fast).",
            "cmd": "nmap -F {target}",
        },
        {
            "name": "Nmap - Full Scan + Service/OS Detection",
            "desc": "Scan every port (1-65535) and try to detect service "
                    "versions and the operating system.",
            "cmd": "nmap -sV -O -p- {target}",
            "requires_root": True,
        },
        {
            "name": "Nmap - Default + Vuln Scripts",
            "desc": "Run Nmap's built-in NSE scripts to flag common known "
                    "vulnerabilities automatically.",
            "cmd": "nmap -sV --script=default,vuln {target}",
        },
        {
            "name": "Whois",
            "desc": "Domain registration lookup (owner, registrar, dates).",
            "cmd": "whois {target}",
        },
        {
            "name": "Dig - DNS Records",
            "desc": "Query all DNS records for the domain.",
            "cmd": "dig {target} ANY",
        },
        {
            "name": "theHarvester - Emails & Subdomains",
            "desc": "Gather emails and subdomains from public sources (OSINT). "
                    "Needs internet access; some sources may return empty "
                    "results if rate-limited.",
            "cmd": "theHarvester -d {target} -b all",
        },
    ],

    "Vulnerability Scanning": [
        {
            "name": "Nikto - Web Server Scan",
            "desc": "Detect dangerous files, outdated software and risky "
                    "configurations on a web server.",
            "cmd": "nikto -h {target}",
        },
        {
            "name": "Dirb - Directory/File Discovery",
            "desc": "Guess hidden directories and files using Dirb's "
                    "built-in default wordlist.",
            "cmd": "dirb http://{target}",
        },
        {
            "name": "Gobuster - Directory Discovery (fast)",
            "desc": "Faster alternative to Dirb. Requires a wordlist file.",
            "cmd": "gobuster dir -u http://{target} -w {wordlist}",
            "requires_wordlist": True,
        },
        {
            "name": "WPScan - WordPress Scan",
            "desc": "Enumerate WordPress plugins, themes, users and known "
                    "vulnerabilities. For full results, configure a free "
                    "WPScan API token (see README). Fails immediately if "
                    "the target is not WordPress.",
            "cmd": "wpscan --url http://{target} --enumerate vp,vt,u",
        },
        {
            "name": "SQLMap - SQL Injection Scan",
            "desc": "Automatically tests a URL for SQL injection and prints "
                    "the DB banner if vulnerable. Target must be a full URL.",
            "cmd": "sqlmap -u {target} --batch --banner",
        },
    ],

    "Password Cracking": [
        {
            "name": "Hydra - SSH Brute Force",
            "desc": "Try every password in the wordlist against SSH "
                    "(username: admin).",
            "cmd": "hydra -l admin -P {wordlist} ssh://{target}",
            "requires_wordlist": True,
        },
        {
            "name": "Hydra - FTP Brute Force",
            "desc": "Try every password in the wordlist against FTP "
                    "(username: admin).",
            "cmd": "hydra -l admin -P {wordlist} ftp://{target}",
            "requires_wordlist": True,
        },
        {
            "name": "Hydra - Web Login Form",
            "desc": "Assumes a login form at '/login' with fields 'user' "
                    "and 'pass', and the string 'incorrect' on failed "
                    "login. You will likely need to edit this template in "
                    "tools_config.py to match the real target form.",
            "cmd": 'hydra -l admin -P {wordlist} {target} http-post-form '
                   '"/login:user=^USER^&pass=^PASS^:F=incorrect"',
            "requires_wordlist": True,
        },
        {
            "name": "John the Ripper - Crack Hash File",
            "desc": "Offline tool: no network target. Put the path to a "
                    "hash file in the Target field, and the wordlist in "
                    "the Wordlist field.",
            "cmd": "john --wordlist={wordlist} {target}",
            "requires_wordlist": True,
        },
    ],

    "Wireless": [
        {
            "name": "Airmon-ng - Enable Monitor Mode",
            "desc": "Switches a wireless adapter into monitor mode. "
                    "Requires a USB Wi-Fi adapter that supports monitor "
                    "mode (most laptop built-in cards and VMs do not). "
                    "Put the interface name (e.g. wlan0) in the Target field.",
            "cmd": "airmon-ng start {target}",
            "requires_root": True,
        },
        {
            "name": "Airodump-ng - Scan Nearby Networks",
            "desc": "Lists nearby Wi-Fi networks. Needs an interface "
                    "already in monitor mode. Put the interface name in "
                    "the Target field.",
            "cmd": "airodump-ng {target}",
            "requires_root": True,
        },
    ],

    "Post-Exploitation": [
        {
            "name": "Netcat - Listener",
            "desc": "Opens a listener on the given port, typically used to "
                    "catch a reverse shell. Put the port number in the "
                    "Wordlist field.",
            "cmd": "nc -lvnp {wordlist}",
            "requires_wordlist": True,
        },
        {
            "name": "Metasploit Framework",
            "desc": "Opens msfconsole. This is a fully interactive tool, "
                    "so it is launched in its own terminal window instead "
                    "of this app's output panel.",
            "cmd": "msfconsole",
            "external_terminal": True,
        },
    ],
}
