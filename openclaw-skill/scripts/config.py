"""Configuration constants for CTF Labs skill"""

from pathlib import Path

# ── Resolved Paths ──────────────────────────────────────────────

SKILL_DIR = Path.home() / ".openclaw" / "skills" / "ctf-labs"
DATA_DIR = SKILL_DIR / "data"
LOGS_DIR = SKILL_DIR / "logs"
CHALLENGES_DIR = SKILL_DIR / "challenges"
SCRIPTS_DIR = SKILL_DIR / "scripts"

# Ensure directories exist at import time
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)
CHALLENGES_DIR.mkdir(parents=True, exist_ok=True)

# ── Docker Configuration ────────────────────────────────────────

DOCKER_NETWORK = "ctf-isolated"
DOCKER_SUBNET = "172.20.0.0/16"
SCHOOL_NETWORK_BLOCK = "10.106.195.0/24"

# ── Resource Limits ─────────────────────────────────────────────

MAX_LABS_PER_USER = 3
MAX_TOTAL_LABS = 50
AUTO_CLEANUP_HOURS = 4
CONTAINER_MEMORY = "2g"
CONTAINER_CPUS = "1"
CONTAINER_PID_LIMIT = 100

# ── Rate Limiting ───────────────────────────────────────────────

RATE_LIMIT_SOFT = 10   # commands per minute
RATE_LIMIT_WARN = 15
RATE_LIMIT_HARD = 20
RATE_LIMIT_BLOCK_SECONDS = 60

# ── Access Control ──────────────────────────────────────────────

ALLOWED_ROLES = ["Operator", "Officer"]
HARDCODED_ADMIN_ID = 393483939194601472

# ── Docker Security Options ─────────────────────────────────────

DOCKER_SECURITY_OPTS = [
    "--security-opt=no-new-privileges",
    "--cap-drop=ALL",
    "--cap-add=NET_BIND_SERVICE",
]

# ── Lab-Specific tmpfs Mounts (writable in-memory, secure) ──────

LAB_TMPFS = {
    "dvwa": [
        "--tmpfs", "/var/lib/mysql:rw,noexec,nosuid,size=100m",
        "--tmpfs", "/var/run/mysqld:rw,noexec,nosuid,size=10m",
        "--tmpfs", "/var/log:rw,noexec,nosuid,size=50m",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=50m",
    ],
    "webgoat": [
        "--tmpfs", "/home/webgoat/.webgoat:rw,noexec,nosuid,size=100m",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=50m",
    ],
    "juice-shop": [
        "--tmpfs", "/juice-shop/data:rw,noexec,nosuid,size=100m",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=50m",
    ],
    "metasploitable": [
        "--tmpfs", "/var/log:rw,noexec,nosuid,size=50m",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=50m",
    ],
    "crypto-lab": [
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",
        "--tmpfs", "/home/challenge:rw,noexec,nosuid,size=50m",
    ],
    "forensics-lab": [
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=100m",
        "--tmpfs", "/home/challenge:rw,noexec,nosuid,size=50m",
    ],
}

# ── Blocked Input Patterns (regex) ──────────────────────────────

BLOCKED_PATTERNS = [
    r'\$\(',              # Command substitution
    r'`[^`]+`',           # Backtick execution
    r'&&|\|\|',           # Command chaining
    r';.*rm',             # Destructive commands
    r'\bcurl\b|\bwget\b', # External fetching
    r'\beval\b|\bexec\b', # Code execution
    r'import\s+os',       # OS module
    r'https?://',         # URL schemes
    r'\bsudo\b',          # Privilege escalation
    r'/etc/passwd',       # Sensitive files
]

# ── Available Lab Types ─────────────────────────────────────────

AVAILABLE_LABS = {
    "dvwa": {
        "name": "Damn Vulnerable Web Application",
        "image": "vulnerables/web-dvwa",
        "category": "web",
        "difficulty": "beginner",
        "port": 80,
        "description": "Practice SQL injection, XSS, command injection",
    },
    "webgoat": {
        "name": "OWASP WebGoat",
        "image": "webgoat/webgoat:latest",
        "category": "web",
        "difficulty": "beginner",
        "port": 8080,
        "description": "OWASP Top 10 practice environment",
    },
    "juice-shop": {
        "name": "OWASP Juice Shop",
        "image": "bkimminich/juice-shop",
        "category": "web",
        "difficulty": "beginner",
        "port": 3000,
        "description": "Modern web application vulnerabilities",
    },
    "metasploitable": {
        "name": "Metasploitable 2",
        "image": "tleemcjr/metasploitable2",
        "category": "system",
        "difficulty": "intermediate",
        "port": 22,
        "description": "Full penetration testing environment",
    },
    "crypto-lab": {
        "name": "Cryptography Lab",
        "image": "custom/crypto-tools",
        "category": "challenge",
        "difficulty": "beginner",
        "port": 7681,
        "description": "Pre-installed crypto tools (hashcat, john, rockyou.txt)",
    },
    "forensics-lab": {
        "name": "Digital Forensics Lab",
        "image": "custom/forensics-tools",
        "category": "challenge",
        "difficulty": "intermediate",
        "port": 7681,
        "description": "Forensics tools (volatility, binwalk, foremost)",
    },
}
