# Available Lab Types

## Network Labs

### kali-lab
- **Image:** `kalilinux/kali-rolling`
- **Description:** Full Kali Linux environment with pre-installed pentesting tools
- **Use Cases:** Network scanning, vulnerability assessment, exploitation practice
- **Default Tools:** nmap, metasploit, burpsuite, sqlmap, john, hashcat, aircrack-ng
- **Memory:** 2GB | **CPUs:** 1 | **PID Limit:** 100

### network-lab
- **Image:** `nicolaka/netshoot`
- **Description:** Lightweight networking troubleshooting toolkit
- **Use Cases:** Network analysis, packet capture, DNS enumeration, traffic inspection
- **Default Tools:** tcpdump, nmap, netcat, dig, curl, iperf, mtr, socat
- **Memory:** 2GB | **CPUs:** 1 | **PID Limit:** 100

## Web Security Labs

### web-lab
- **Image:** `vulnerables/web-dvwa`
- **Description:** Damn Vulnerable Web Application for practicing web exploits
- **Use Cases:** SQL injection, XSS, CSRF, file inclusion, command injection
- **Exposed Port:** 80 (HTTP)
- **Memory:** 2GB | **CPUs:** 1 | **PID Limit:** 100

## Cryptography & Forensics Labs

### crypto-lab
- **Image:** `remnux/remnux-distro`
- **Description:** REMnux distribution focused on reverse engineering and crypto analysis
- **Use Cases:** Malware analysis, cryptographic challenges, encoding/decoding
- **Default Tools:** openssl, hashcat, john, CyberChef (CLI), python3 crypto libs
- **Memory:** 2GB | **CPUs:** 1 | **PID Limit:** 100

### forensics-lab
- **Image:** `remnux/remnux-distro`
- **Description:** Digital forensics environment with analysis tools
- **Use Cases:** Disk forensics, memory analysis, file carving, steganography
- **Default Tools:** volatility, autopsy, binwalk, foremost, exiftool, steghide
- **Memory:** 2GB | **CPUs:** 1 | **PID Limit:** 100

## OSINT Labs

### osint-lab
- **Image:** `tracelabs/tlosint-live`
- **Description:** Trace Labs OSINT VM for open source intelligence gathering
- **Use Cases:** Social media investigation, domain reconnaissance, email tracing
- **Default Tools:** Maltego, theHarvester, sherlock, recon-ng, spiderfoot
- **Memory:** 2GB | **CPUs:** 1 | **PID Limit:** 100

---

## Resource Limits (All Labs)

| Resource | Limit |
|----------|-------|
| Memory | 2 GB |
| CPUs | 1 core |
| PIDs | 100 |
| Max per user | 3 |
| Max total | 50 |
| Auto-cleanup | 4 hours |

## Security Controls

All labs run with:
- `--cap-drop=ALL` (drop all Linux capabilities)
- `--cap-add=NET_BIND_SERVICE` (allow binding to low ports only)
- `--read-only` root filesystem
- `--tmpfs=/tmp:rw,noexec,nosuid` (writable temp, no exec)
- `--security-opt=no-new-privileges` (prevent privilege escalation)
- `--network=ctf-isolated` (isolated Docker network)
- Outbound traffic to school network (10.106.195.0/24) blocked via iptables
