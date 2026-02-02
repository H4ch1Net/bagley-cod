# Bagley

AI-powered bot for spinning up CTF practice labs on demand.

## Why this exists

Setting up vulnerable environments for CTF practice normally means:
- Manually running Docker commands
- Remembering which ports and IPs you used
- Cleaning up containers when you're done

Bagley handles all that. Just tell it what you need in plain English and it sets everything up.

## What it does

- Spins up vulnerable lab environments (DVWA, WebGoat, Metasploitable, Juice Shop)
- Understands natural language ("I need a DVWA instance" → starts one)
- Tracks active labs and who's using them
- Auto-cleanup when you're done

## Status

**Work in progress.** The orchestration logic and AI integration work. Docker deployment coming soon.

Right now it simulates labs — when deployed, it'll actually spin up real containers.

## Usage

### Via Discord (when deployed)

```
@Bagley start dvwa
→ ✅ dvwa-mauro-1 started at 192.168.100.50

@Bagley what's running?
→ 📋 You have DVWA running for 2 hours

@Bagley stop dvwa
→ 🛑 dvwa-mauro-1 stopped
```

### Via CLI (for testing now)

```bash
python tools/cli.py

> list
🔬 Available Lab Types:
• DVWA - Damn Vulnerable Web App (beginner)
• WEBGOAT - WebGoat (beginner)
• METASPLOITABLE - Metasploitable 2 (intermediate)
• JUICE-SHOP - OWASP Juice Shop (beginner)

> start dvwa
✅ dvwa-mauro-1 started successfully
📍 IP: 192.168.100.135
🔗 Access: http://192.168.100.135

> status
📋 Active Labs:
🟢 dvwa-mauro-1 | 192.168.100.135 | Uptime: 0:15:32
```

## Available Labs

| Lab | Focus Area | Difficulty |
|-----|-----------|------------|
| **DVWA** | SQL injection, XSS, command injection | Beginner |
| **WebGoat** | OWASP Top 10 practice | Beginner |
| **Metasploitable** | Full pentesting environment | Intermediate |
| **Juice Shop** | Modern web app vulnerabilities | Beginner |

## Setup

**Requirements:**
- Python 3.8+
- `pip`

**Install:**
```bash
git clone https://github.com/your-username/bagley.git
cd bagley
pip install -r requirements.txt
```

**Run:**
```bash
# Using the helper script (recommended)
./run.sh

# Or manually with PYTHONPATH
PYTHONPATH=. python3 tools/cli.py
```

For AI features, you'll need an OpenRouter API key. Ask the maintainer.

## How it works

```
You: "start dvwa"
  ↓
AI figures out what you mean
  ↓
Orchestrator spins up container (simulated for now)
  ↓
You get an IP to hack
```

**Stack:**
- Python for orchestration
- OpenRouter API for natural language processing
- Docker for containers (coming soon)
- Discord for the bot interface (coming soon)

## Project Structure

```
bagley/
├── skills/
│   ├── lab_orchestrator.py    # Manages lab lifecycle
│   └── ai_integration.py      # Handles AI parsing
├── tools/
│   └── cli.py                 # CLI interface
├── docs/
│   └── PROJECT_PLAN.md        # Roadmap
└── requirements.txt
```

## Roadmap

- [x] Core orchestration logic
- [x] AI command parsing
- [x] CLI interface
- [ ] Docker integration
- [ ] Discord bot deployment
- [ ] Auto-shutdown timers
- [ ] Usage tracking

## Contributing

This is a small club project. If you want to help, just reach out.

## License

MIT - do whatever you want with it.

---

Built for CTF practice at a cybersecurity club.
