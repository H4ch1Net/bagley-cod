#!/usr/bin/env python3
"""User statistics, leaderboard, and progress tracking.

All public functions are accessible via CLI and return JSON to stdout.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from config import DATA_DIR, LOGS_DIR

# ── Logging ─────────────────────────────────────────────────────

audit_logger = logging.getLogger("audit")
audit_logger.setLevel(logging.INFO)
_ah = logging.FileHandler(LOGS_DIR / "audit.log")
_ah.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
audit_logger.addHandler(_ah)

error_logger = logging.getLogger("errors")
error_logger.setLevel(logging.ERROR)
_eh = logging.FileHandler(LOGS_DIR / "errors.log")
_eh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
error_logger.addHandler(_eh)

# ── Persistence ─────────────────────────────────────────────────

STATS_FILE = DATA_DIR / "user_stats.json"


def _load_stats() -> Dict:
    if STATS_FILE.exists():
        try:
            return json.loads(STATS_FILE.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_stats(data: Dict) -> None:
    STATS_FILE.write_text(json.dumps(data, indent=2))


def _ensure_user(stats: Dict, username: str) -> Dict:
    """Make sure a user entry exists, return it."""
    if username not in stats:
        stats[username] = {
            "total_points": 0,
            "solves": [],
            "categories": {},
            "labs_started": 0,
            "first_seen": datetime.now().isoformat(),
        }
    return stats[username]


# ── Public Commands ─────────────────────────────────────────────


def leaderboard(limit: int = 10) -> Dict[str, Any]:
    """Return top players sorted by total points."""
    stats = _load_stats()

    # Sort by total points descending
    ranked = sorted(stats.items(), key=lambda x: x[1].get("total_points", 0), reverse=True)
    ranked = ranked[:limit]

    board = []
    for rank, (username, data) in enumerate(ranked, 1):
        board.append({
            "rank": rank,
            "username": username,
            "points": data.get("total_points", 0),
            "solves": len(data.get("solves", [])),
        })

    return {"success": True, "leaderboard": board}


def user_stats(username: str) -> Dict[str, Any]:
    """Return detailed statistics for a user."""
    stats = _load_stats()
    data = stats.get(username)

    if not data:
        return {
            "success": True,
            "username": username,
            "message": f"No stats for {username}. Start solving challenges!",
        }

    # Last 5 solves
    recent = sorted(data.get("solves", []), key=lambda s: s.get("timestamp", ""), reverse=True)[:5]

    return {
        "success": True,
        "username": username,
        "total_points": data.get("total_points", 0),
        "challenges_solved": len(data.get("solves", [])),
        "labs_started": data.get("labs_started", 0),
        "categories": data.get("categories", {}),
        "recent_solves": recent,
        "first_seen": data.get("first_seen", "unknown"),
    }


def record_solve(username: str, challenge_id: str, points: int, category: str) -> Dict[str, Any]:
    """Record a successful challenge solve (called by challenge_manager)."""
    stats = _load_stats()
    user = _ensure_user(stats, username)

    # Duplicate check
    solved_ids = [s["challenge_id"] for s in user.get("solves", [])]
    if challenge_id in solved_ids:
        return {"success": False, "error": "Already solved"}

    user["total_points"] += points
    user["solves"].append({
        "challenge_id": challenge_id,
        "points": points,
        "category": category,
        "timestamp": datetime.now().isoformat(),
    })
    if category not in user["categories"]:
        user["categories"][category] = 0
    user["categories"][category] += points

    _save_stats(stats)
    audit_logger.info(f"SOLVE_RECORDED - User: {username} - {challenge_id} +{points}pts")
    return {"success": True, "total_points": user["total_points"]}


def record_lab_start(username: str) -> Dict[str, Any]:
    """Increment lab start counter for a user."""
    stats = _load_stats()
    user = _ensure_user(stats, username)
    user["labs_started"] += 1
    _save_stats(stats)
    return {"success": True, "labs_started": user["labs_started"]}


# ── CLI Dispatch ────────────────────────────────────────────────


def _output(data: Dict[str, Any]) -> None:
    print(json.dumps(data))


def main() -> None:
    if len(sys.argv) < 2:
        _output({"success": False, "error": "Usage: stats_manager.py <action> [args...]"})
        sys.exit(1)

    action = sys.argv[1]

    try:
        if action == "leaderboard":
            limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
            _output(leaderboard(limit))

        elif action == "stats":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: stats <username>"})
                sys.exit(1)
            _output(user_stats(sys.argv[2]))

        elif action == "record_solve":
            if len(sys.argv) < 6:
                _output({"success": False, "error": "Usage: record_solve <username> <challenge_id> <points> <category>"})
                sys.exit(1)
            _output(record_solve(sys.argv[2], sys.argv[3], int(sys.argv[4]), sys.argv[5]))

        elif action == "record_lab_start":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: record_lab_start <username>"})
                sys.exit(1)
            _output(record_lab_start(sys.argv[2]))

        else:
            _output({"success": False, "error": f"Unknown action: {action}"})
            sys.exit(1)

    except Exception as exc:
        error_logger.error(f"stats_manager.py {action} failed: {exc}", exc_info=True)
        _output({"success": False, "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
