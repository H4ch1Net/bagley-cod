# Security Policy

## Access Control

### Roles
- **Operator** — Standard club members. Can start/stop their own labs, solve challenges, view stats.
- **Officer** — Club officers. All Operator permissions plus: force-cleanup any user's labs, view server stats, verify new members.

### Admin Override
- Discord User ID `393483939194601472` has full access regardless of roles.
- This is hardcoded in `scripts/config.py` as `HARDCODED_ADMIN_ID`.

### Verified Users
- Users can be added to `data/verified_users.json` via the `verify_member` command.
- Verified users gain Operator-level access without needing Discord roles.
- Only Officers and the hardcoded admin can verify new members.

## Input Sanitization

All user inputs are validated against a blocklist of dangerous patterns before processing:

### Blocked Patterns
- Shell injection: `; && || | \` $() \`\``
- Path traversal: `../`
- Docker escape attempts: `docker`, `mount`, `chroot`, `nsenter`
- Privilege escalation: `sudo`, `su `
- System modification: `rm -rf`, `chmod`, `chown`, `mkfs`
- Network abuse: `nc -e`, `ncat`, `reverse shell`, `bind shell`

Any input matching these patterns is rejected with an error before reaching any command execution.

## Rate Limiting

File-based rate limiting prevents abuse. Thresholds per user per 60-second window:

| Level | Requests/min | Action |
|-------|-------------|--------|
| **Normal** | ≤ 10 | Allowed silently |
| **Soft** | 11-14 | Allowed with warning |
| **Warn** | 15-19 | Allowed with strong warning |
| **Hard** | ≥ 20 | Blocked for 60 seconds |

Rate limit state is stored in `data/rate_limits.json` and persists across process invocations.

## Container Security

Every Docker container runs with defense-in-depth:

### Capability Restrictions
```
--cap-drop=ALL
--cap-add=NET_BIND_SERVICE
--security-opt=no-new-privileges
```

### Filesystem Protection
```
--read-only
--tmpfs=/tmp:rw,noexec,nosuid
```

### Resource Limits
```
--memory=2g
--cpus=1
--pids-limit=100
```

### Network Isolation
- All labs run on a dedicated Docker network: `ctf-isolated` (172.20.0.0/16)
- Outbound traffic to school network `10.106.195.0/24` is blocked via iptables
- Inter-container communication is allowed within the isolated network
- Internet access is available (for tool updates, package installs)

### Container Naming
- Format: `ctf-<username>-<lab_type>`
- Prevents name collisions and enables per-user tracking

## Auto-Cleanup

- Labs running longer than 4 hours are automatically stopped and removed
- The `auto_cleanup` command should be called periodically (recommended: every 15 minutes)
- Cleanup removes both the Docker container and the tracking entry in `data/active_labs.json`

## Audit Logging

All security-relevant events are logged to `logs/audit.log`:
- Access checks (granted/denied)
- Rate limit violations
- Lab starts/stops
- Container force-cleanups
- Member verifications
- Input sanitization failures

Log format: `[ISO-8601 timestamp] EVENT_TYPE | username | details`

## Incident Response

If suspicious activity is detected:
1. Check `logs/audit.log` for patterns
2. Use `force_cleanup <username>` to terminate all user labs
3. Remove user from `data/verified_users.json` if needed
4. Review Docker logs: `docker logs ctf-<username>-<lab_type>`
5. Check network activity: `docker exec <container> netstat -tlnp`
