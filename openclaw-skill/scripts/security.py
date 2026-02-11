#!/usr/bin/env python3
"""Security module: access control, input sanitization, rate limiting, audit logging."""

import json
import logging
import re
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

from config import (
    ALLOWED_ROLES,
    BLOCKED_PATTERNS,
    DATA_DIR,
    HARDCODED_ADMIN_ID,
    LOGS_DIR,
    RATE_LIMIT_BLOCK_SECONDS,
    RATE_LIMIT_HARD,
    RATE_LIMIT_SOFT,
    RATE_LIMIT_WARN,
)

# ── Logging Setup ───────────────────────────────────────────────

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
_audit_handler = logging.FileHandler(LOGS_DIR / "audit.log")
_audit_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
audit_logger.addHandler(_audit_handler)

error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
_error_handler = logging.FileHandler(LOGS_DIR / "errors.log")
_error_handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
error_logger.addHandler(_error_handler)

# ── File Helpers ────────────────────────────────────────────────

RATE_LIMITS_FILE = DATA_DIR / "rate_limits.json"
VERIFIED_USERS_FILE = DATA_DIR / "verified_users.json"


def _load_json(path: Path) -> Dict:
    if path.exists():
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_json(path: Path, data: Dict) -> None:
    path.write_text(json.dumps(data, indent=2))


# ── Access Control ──────────────────────────────────────────────


def check_access(username: str, user_id: str, roles_csv: str) -> Dict[str, Any]:
    """
    Validate whether user has permission to use CTF labs.

    Args:
        username: Discord display name
        user_id: Discord user ID (numeric string)
        roles_csv: Comma-separated list of Discord role names
    """
    try:
        uid = int(user_id)
    except (ValueError, TypeError):
        uid = 0

    # Hardcoded admin bypass – Discord guarantees this ID
    if uid == HARDCODED_ADMIN_ID:
        audit_logger.info(f"ACCESS_GRANTED (admin) - User: {username} ID: {user_id}")
        return {"allowed": True, "admin": True}

    # Check Discord roles
    roles: List[str] = [r.strip() for r in roles_csv.split(",") if r.strip()] if roles_csv else []

    if any(role in ALLOWED_ROLES for role in roles):
        audit_logger.info(f"ACCESS_GRANTED - User: {username} Roles: {roles}")
        return {"allowed": True}

    # Check local verified-users list (officer-granted)
    verified = _load_json(VERIFIED_USERS_FILE)
    if user_id in verified or username in verified:
        audit_logger.info(f"ACCESS_GRANTED (verified) - User: {username}")
        return {"allowed": True}

    # Denied
    audit_logger.warning(f"UNVERIFIED_ACCESS - User: {username} ID: {user_id} Roles: {roles}")
    return {
        "allowed": False,
        "reason": "no_role",
        "message": (
            "👋 Hey! You need to be verified to use CTF labs.\n\n"
            "To get access:\n"
            "1. Contact @officers in the Discord server\n"
            "2. They'll give you the @Operator role\n"
            "3. Then you can start labs!\n\n"
            "This helps us keep the labs secure 🔒"
        ),
    }


# ── Input Sanitization ─────────────────────────────────────────


def sanitize(user_input: str) -> Dict[str, Any]:
    """
    Validate and sanitize user input against injection patterns.

    Args:
        user_input: Raw string from user
    """
    if not user_input or not user_input.strip():
        return {"valid": False, "reason": "Empty input"}

    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            audit_logger.warning(
                f"BLOCKED_INPUT - Pattern: {pattern} - Input: {user_input[:80]}"
            )
            return {"valid": False, "reason": "Invalid input detected", "pattern": pattern}

    cleaned = user_input.strip()
    return {"valid": True, "cleaned": cleaned}


# ── Rate Limiting ───────────────────────────────────────────────


def rate_limit(username: str) -> Dict[str, Any]:
    """
    Track and enforce per-user rate limits.

    Uses file-based timestamp tracking since each CLI invocation is a
    separate process.
    """
    now = time.time()
    cutoff = now - 60.0  # 1-minute window

    data = _load_json(RATE_LIMITS_FILE)

    # Per-user entry: {"timestamps": [...], "blocked_until": <epoch|null>, "warned": bool}
    entry = data.get(username, {"timestamps": [], "blocked_until": None, "warned": False})

    # Check active block
    blocked_until = entry.get("blocked_until")
    if blocked_until and now < blocked_until:
        remaining = int(blocked_until - now)
        audit_logger.warning(f"RATE_LIMIT_BLOCKED - User: {username} - Wait: {remaining}s")
        return {"allowed": False, "wait_seconds": remaining}

    # Clean stale timestamps
    timestamps = [t for t in entry.get("timestamps", []) if t > cutoff]
    count = len(timestamps)

    # Hard limit – block for 60 seconds
    if count >= RATE_LIMIT_HARD:
        entry["blocked_until"] = now + RATE_LIMIT_BLOCK_SECONDS
        entry["timestamps"] = timestamps
        entry["warned"] = False
        data[username] = entry
        _save_json(RATE_LIMITS_FILE, data)
        audit_logger.warning(f"RATE_LIMIT_EXCEEDED - User: {username} - Count: {count}")
        return {"allowed": False, "wait_seconds": RATE_LIMIT_BLOCK_SECONDS}

    # Record this request
    timestamps.append(now)
    entry["timestamps"] = timestamps
    entry["blocked_until"] = None

    # Warning threshold
    warning = None
    if count >= RATE_LIMIT_WARN and not entry.get("warned"):
        warning = "⚠️ You're sending commands quickly. Please slow down."
        entry["warned"] = True
    elif count < RATE_LIMIT_SOFT:
        entry["warned"] = False

    data[username] = entry
    _save_json(RATE_LIMITS_FILE, data)

    result: Dict[str, Any] = {"allowed": True}
    if warning:
        result["warning"] = warning
    return result


# ── Member Verification (Officer Command) ──────────────────────


def verify_member(username: str, user_id: str) -> Dict[str, Any]:
    """
    Grant a user local @Operator-equivalent access.

    Persists to verified_users.json so the user is allowed on future calls
    even if their Discord roles aren't passed.
    """
    verified = _load_json(VERIFIED_USERS_FILE)
    verified[user_id] = {
        "username": username,
        "verified_at": datetime.now().isoformat(),
    }
    _save_json(VERIFIED_USERS_FILE, verified)
    audit_logger.info(f"MEMBER_VERIFIED - User: {username} ID: {user_id}")
    return {"success": True, "message": f"✅ {username} has been verified for CTF labs."}


# ── Audit Logging Helper ───────────────────────────────────────


def log_security_event(event_type: str, username: str, details: str) -> Dict[str, Any]:
    """Write a security event to the audit log."""
    audit_logger.info(f"{event_type} - User: {username} - {details}")
    return {"success": True}


# ── CLI Dispatch ────────────────────────────────────────────────


def _output(data: Dict[str, Any]) -> None:
    print(json.dumps(data))


def main() -> None:
    if len(sys.argv) < 2:
        _output({"success": False, "error": "Usage: security.py <action> [args...]"})
        sys.exit(1)

    action = sys.argv[1]

    try:
        if action == "check_access":
            if len(sys.argv) < 5:
                _output({"success": False, "error": "Usage: check_access <username> <user_id> <roles_csv>"})
                sys.exit(1)
            _output(check_access(sys.argv[2], sys.argv[3], sys.argv[4]))

        elif action == "sanitize":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: sanitize <input>"})
                sys.exit(1)
            _output(sanitize(sys.argv[2]))

        elif action == "rate_limit":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: rate_limit <username>"})
                sys.exit(1)
            _output(rate_limit(sys.argv[2]))

        elif action == "verify_member":
            if len(sys.argv) < 4:
                _output({"success": False, "error": "Usage: verify_member <username> <user_id>"})
                sys.exit(1)
            _output(verify_member(sys.argv[2], sys.argv[3]))

        elif action == "log_event":
            if len(sys.argv) < 5:
                _output({"success": False, "error": "Usage: log_event <type> <username> <details>"})
                sys.exit(1)
            _output(log_security_event(sys.argv[2], sys.argv[3], sys.argv[4]))

        else:
            _output({"success": False, "error": f"Unknown action: {action}"})
            sys.exit(1)

    except Exception as exc:
        error_logger.error(f"security.py {action} failed: {exc}", exc_info=True)
        _output({"success": False, "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
