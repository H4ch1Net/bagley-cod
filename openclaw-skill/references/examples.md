# Usage Examples

## Lab Management

### Starting a Lab
```
User: "Start a Kali lab for me"

OpenClaw runs:
  python3 scripts/security.py check_access johndoe 123456789 "Operator,Member"
  python3 scripts/security.py rate_limit johndoe
  python3 scripts/lab_orchestrator.py start johndoe kali-lab

Response:
  🚀 Lab Deployed!
  • Type: kali-lab
  • Container: ctf-johndoe-kali-lab
  • IP: 172.20.0.2
  • Auto-shutdown: 4 hours
  • Run `status` to check your labs anytime!
```

### Checking Lab Status
```
User: "What labs do I have running?"

OpenClaw runs:
  python3 scripts/lab_orchestrator.py status johndoe

Response:
  📊 Your Active Labs:

  1. kali-lab
     • Container: ctf-johndoe-kali-lab
     • IP: 172.20.0.2
     • Uptime: 45 minutes
     • Time remaining: 3h 15m

  💡 You have 2 lab slots remaining.
```

### Stopping a Lab
```
User: "Stop my kali lab"

OpenClaw runs:
  python3 scripts/lab_orchestrator.py stop johndoe kali-lab

Response:
  🛑 Lab Stopped
  • kali-lab has been shut down and cleaned up.
  • You now have 3 available lab slots.
```

### Listing Available Labs
```
User: "What labs can I spin up?"

OpenClaw runs:
  python3 scripts/lab_orchestrator.py list

Response:
  🧪 Available Lab Types:

  • kali-lab — Full Kali Linux pentesting environment
  • network-lab — Network troubleshooting toolkit
  • web-lab — DVWA vulnerable web application
  • crypto-lab — Cryptography and reverse engineering tools
  • forensics-lab — Digital forensics analysis suite
  • osint-lab — Open source intelligence gathering
```

## Challenges

### Viewing Categories
```
User: "What challenge categories are there?"

OpenClaw runs:
  python3 scripts/challenge_manager.py list_categories

Response:
  📂 Challenge Categories:
  • cryptography (3 challenges)
  • forensics (2 challenges)
  • osint (2 challenges)
  • password-cracking (2 challenges)
  • web (2 challenges)
```

### Browsing Challenges
```
User: "Show me the cryptography challenges"

OpenClaw runs:
  python3 scripts/challenge_manager.py list_challenges cryptography

Response:
  🔐 Cryptography Challenges:

  1. Caesar's Secret (crypto-001) — Easy — 100 pts
  2. Not So Secret Encoding (crypto-002) — Easy — 75 pts
  3. Hash Identification (crypto-003) — Easy — 100 pts

  Use `get_challenge <id>` to see full details!
```

### Solving a Challenge
```
User: "I want to submit flag{the_quick_brown_fox_jumps_over_the_lazy_dog} for caesar-001... wait, it's crypto-001"

OpenClaw runs:
  python3 scripts/challenge_manager.py solve johndoe crypto-001 "flag{the_quick_brown_fox_jumps_over_the_lazy_dog}"

Response:
  🎉 Correct! Caesar's Secret solved!
  • Points earned: 100
  • Your total: 100 points
  • Category progress: cryptography 1/3
```

## Stats & Leaderboard

### Viewing the Leaderboard
```
User: "Show me the leaderboard"

OpenClaw runs:
  python3 scripts/stats_manager.py leaderboard 10

Response:
  🏆 CTF Leaderboard (Top 10):

  1. 🥇 h4ch1 — 1,250 pts (15 solves)
  2. 🥈 cyb3rcat — 900 pts (10 solves)
  3. 🥉 n3trunner — 750 pts (8 solves)
  4.    nullbyte — 500 pts (6 solves)
  5.    hacksaw — 350 pts (4 solves)
```

### Personal Stats
```
User: "Show my stats"

OpenClaw runs:
  python3 scripts/stats_manager.py stats johndoe

Response:
  📈 Stats for johndoe:
  • Total Points: 450
  • Challenges Solved: 5
  • Labs Started: 12
  • Top Category: cryptography (3 solves)
  • Recent: Hash Identification, Caesar's Secret
```

## Officer Commands

### Force Cleanup
```
Officer: "Clean up all of baduser's labs"

OpenClaw runs:
  python3 scripts/security.py check_access officer123 987654321 "Officer,Operator"
  python3 scripts/lab_orchestrator.py force_cleanup baduser

Response:
  🧹 Force Cleanup Complete
  • Removed 2 labs for baduser
  • Containers cleaned: ctf-baduser-kali-lab, ctf-baduser-web-lab
```

### Server Stats
```
Officer: "How's the server doing?"

OpenClaw runs:
  python3 scripts/lab_orchestrator.py server_stats

Response:
  🖥️ Server Status:
  • Docker Disk: 15.2 GB used
  • Memory: 42 GB / 126 GB (33%)
  • CPU Cores: 32
  • GPU: NVIDIA RTX 4090 (78°C)
  • Active Containers: 8 / 50 max
```

## Error Handling

### Access Denied
```
Response:
  🚫 Access Denied
  You need the Operator or Officer role.
  Ask a club officer to verify you with the verify_member command.
```

### Rate Limited
```
Response:
  ⏳ Slow down!
  You've hit the rate limit (20 requests/minute).
  Please wait 60 seconds before trying again.
```

### Invalid Input
```
Response:
  ⚠️ Invalid Input
  Your input contains blocked patterns for security.
  Please remove special characters and try again.
```
