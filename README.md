# Bagley

Production-ready Discord bot for managing CTF practice labs with Docker containers.

## What it does

- Spins up isolated vulnerable lab environments (DVWA, WebGoat, Metasploitable, Juice Shop)
- Understands natural language via OpenRouter AI ("I need a DVWA instance" → starts one)
- Challenge system with flag submission and point tracking
- Leaderboard and per-user statistics
- Auto-cleanup of idle containers after 4 hours
- Rate limiting, input sanitization, and role-based access control
- Systemd service for reliable deployment

## Available Labs

| Lab | Focus Area | Difficulty | Port |
|-----|-----------|------------|------|
| **DVWA** | SQL injection, XSS, command injection | Beginner | 80 |
| **WebGoat** | OWASP Top 10 practice | Beginner | 8080 |
| **Juice Shop** | Modern web app vulnerabilities | Beginner | 3000 |
| **Metasploitable** | Full pentesting environment | Intermediate | 22 |

## Project Structure

```
bagley/
├── config/
│   ├── __init__.py
│   ├── security.py          # Security configurations
│   └── settings.py          # General settings
├── skills/
│   ├── __init__.py
│   ├── lab_orchestrator.py  # Docker management
│   ├── challenge_manager.py # Challenge system
│   ├── stats_manager.py     # User statistics
│   └── ai_integration.py    # OpenRouter API
├── discord_bot/
│   ├── __init__.py
│   ├── bot.py               # Main bot file
│   ├── commands.py          # Command helpers
│   └── utils.py             # Rate limiter & utilities
├── challenges/
│   ├── cryptography/
│   ├── osint/
│   ├── password-cracking/
│   ├── forensics/
│   └── web/
├── data/
│   └── user_stats.json
├── logs/
├── tests/
│   ├── test_orchestrator.py
│   └── test_challenges.py
├── tools/
│   └── cli.py               # CLI interface (testing)
├── .env.example
├── requirements.txt
├── bagley-bot.service
└── README.md
```

## Setup

### Requirements
- Python 3.12+
- Docker
- Discord Bot Token

### Install

```bash
git clone https://github.com/your-username/bagley.git
cd bagley
pip3 install -r requirements.txt
```

### Configure

```bash
cp .env.example .env
# Edit .env with your tokens
```

### Docker Network Setup

```bash
docker network create --subnet=172.20.0.0/16 ctf-isolated
```

### Pull Lab Images

```bash
docker pull vulnerables/web-dvwa
docker pull webgoat/webgoat:latest
docker pull bkimminich/juice-shop
docker pull tleemcjr/metasploitable2
```

## Usage

### Discord Commands

```
!start <lab>         - Start a CTF lab
!stop <lab>          - Stop a running lab
!delete <lab>        - Delete a lab
!status              - Check your active labs
!list                - List available labs
!categories          - List challenge categories
!challenges <cat>    - List challenges in category
!solve <id> <flag>   - Submit a flag
!leaderboard         - Top players
!stats [user]        - User statistics
!help                - Show all commands
```

### Examples

```
!start dvwa
→ ✅ dvwa-h4ch1-1234 started successfully!
  📍 IP: 172.20.0.2
  🔗 Access: http://172.20.0.2:80

!status
→ 📋 Your Active Labs:
  🟢 dvwa | 172.20.0.2:80 | Uptime: 0h 15m

!solve crypto-001 flag{the_quick_brown_fox_jumps_over_the_lazy_dog}
→ ✅ Correct! Flag accepted!
  🎉 +100 points
```

### CLI (for testing)

```bash
PYTHONPATH=. python3 tools/cli.py
```

## Security

- **Container Hardening:** no-new-privileges, dropped capabilities, read-only rootfs, memory/CPU/PID limits
- **Input Sanitization:** blocks command injection, URL schemes, eval/exec patterns
- **Rate Limiting:** 10/min soft → 15/min warn → 20/min hard block
- **Role-Based Access:** requires `@verified-member` role for lab commands
- **Isolated Network:** containers run on dedicated Docker network

## Deployment

```bash
# 1. Install service
sudo cp bagley-bot.service /etc/systemd/system/
sudo systemctl daemon-reload

# 2. Enable and start
sudo systemctl enable bagley-bot
sudo systemctl start bagley-bot

# 3. Check status
sudo systemctl status bagley-bot

# 4. View logs
journalctl -u bagley-bot -f
```

## Testing

```bash
PYTHONPATH=. python3 tests/test_orchestrator.py
PYTHONPATH=. python3 tests/test_challenges.py
```

## License

MIT

---

Built for a cybersecurity club.
