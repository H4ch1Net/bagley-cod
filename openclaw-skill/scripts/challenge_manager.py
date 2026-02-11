#!/usr/bin/env python3
"""Challenge loading, listing, and flag validation.

All public functions are accessible via CLI and return JSON to stdout.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import CHALLENGES_DIR, DATA_DIR, LOGS_DIR

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

# ── Stats Helper (inline import avoidance) ──────────────────────

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


# ── Challenge Loading ───────────────────────────────────────────


def _load_all_challenges() -> Dict[str, dict]:
    """Load every challenge JSON from the challenges/ tree."""
    challenges: Dict[str, dict] = {}

    if not CHALLENGES_DIR.exists():
        return challenges

    for category_dir in CHALLENGES_DIR.iterdir():
        if not category_dir.is_dir():
            continue
        for challenge_file in category_dir.glob("*.json"):
            try:
                data = json.loads(challenge_file.read_text())
                cid = data.get("id")
                if cid:
                    challenges[cid] = data
            except (json.JSONDecodeError, OSError) as exc:
                error_logger.error(f"Bad challenge file {challenge_file}: {exc}")

    return challenges


# ── Public Commands ─────────────────────────────────────────────


def list_categories() -> Dict[str, Any]:
    """Return all unique challenge categories."""
    challenges = _load_all_challenges()
    cats = sorted({c.get("category", "uncategorized") for c in challenges.values()})
    return {"success": True, "categories": cats, "count": len(cats)}


def list_challenges(category: str) -> Dict[str, Any]:
    """Return challenges in a specific category, sorted by points."""
    challenges = _load_all_challenges()
    filtered = [
        c for c in challenges.values()
        if c.get("category", "").lower() == category.lower()
    ]

    if not filtered:
        return {"success": True, "challenges": [], "message": f"No challenges in category: {category}"}

    filtered.sort(key=lambda c: c.get("points", 0))

    items = []
    for c in filtered:
        items.append({
            "id": c["id"],
            "title": c.get("title", "Untitled"),
            "difficulty": c.get("difficulty", "unknown"),
            "points": c.get("points", 0),
            "description": c.get("description", ""),
        })

    return {"success": True, "category": category, "challenges": items, "count": len(items)}


def get_challenge(challenge_id: str) -> Dict[str, Any]:
    """Return full details for a challenge (excluding the flag)."""
    challenges = _load_all_challenges()
    c = challenges.get(challenge_id)

    if not c:
        return {"success": False, "error": f"Challenge not found: {challenge_id}"}

    return {
        "success": True,
        "challenge": {
            "id": c["id"],
            "title": c.get("title"),
            "category": c.get("category"),
            "difficulty": c.get("difficulty"),
            "points": c.get("points", 0),
            "description": c.get("description"),
            "hints": c.get("hints", []),
            "resources": c.get("resources", []),
        },
    }


def solve(username: str, challenge_id: str, flag: str) -> Dict[str, Any]:
    """Validate a flag submission, award points if correct."""
    challenges = _load_all_challenges()
    c = challenges.get(challenge_id)

    if not c:
        return {"success": True, "correct": False, "message": f"Challenge not found: {challenge_id}"}

    # Check for duplicate solve
    stats = _load_stats()
    user = stats.get(username, {})
    solved_ids = [s["challenge_id"] for s in user.get("solves", [])]
    if challenge_id in solved_ids:
        return {"success": True, "correct": False, "message": "You've already solved this challenge."}

    # Validate flag
    correct_flag = c.get("flag", "")
    if flag.strip() != correct_flag:
        audit_logger.info(f"FLAG_INCORRECT - User: {username} - Challenge: {challenge_id}")
        return {"success": True, "correct": False, "message": "Incorrect flag. Try again!"}

    # Award points
    points = c.get("points", 0)
    category = c.get("category", "unknown")

    # Update stats inline (avoid circular imports with stats_manager)
    from datetime import datetime

    if username not in stats:
        stats[username] = {
            "total_points": 0,
            "solves": [],
            "categories": {},
            "labs_started": 0,
            "first_seen": datetime.now().isoformat(),
        }

    stats[username]["total_points"] += points
    stats[username]["solves"].append({
        "challenge_id": challenge_id,
        "points": points,
        "category": category,
        "timestamp": datetime.now().isoformat(),
    })

    if category not in stats[username]["categories"]:
        stats[username]["categories"][category] = 0
    stats[username]["categories"][category] += points

    _save_stats(stats)

    audit_logger.info(
        f"FLAG_CORRECT - User: {username} - Challenge: {challenge_id} - Points: +{points}"
    )

    return {
        "success": True,
        "correct": True,
        "points_awarded": points,
        "total_points": stats[username]["total_points"],
        "message": f"Correct! +{points} points",
    }


# ── CLI Dispatch ────────────────────────────────────────────────


def _output(data: Dict[str, Any]) -> None:
    print(json.dumps(data))


def main() -> None:
    if len(sys.argv) < 2:
        _output({"success": False, "error": "Usage: challenge_manager.py <action> [args...]"})
        sys.exit(1)

    action = sys.argv[1]

    try:
        if action == "list_categories":
            _output(list_categories())

        elif action == "list_challenges":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: list_challenges <category>"})
                sys.exit(1)
            _output(list_challenges(sys.argv[2]))

        elif action == "get_challenge":
            if len(sys.argv) < 3:
                _output({"success": False, "error": "Usage: get_challenge <challenge_id>"})
                sys.exit(1)
            _output(get_challenge(sys.argv[2]))

        elif action == "solve":
            if len(sys.argv) < 5:
                _output({"success": False, "error": 'Usage: solve <username> <challenge_id> "<flag>"'})
                sys.exit(1)
            _output(solve(sys.argv[2], sys.argv[3], sys.argv[4]))

        else:
            _output({"success": False, "error": f"Unknown action: {action}"})
            sys.exit(1)

    except Exception as exc:
        error_logger.error(f"challenge_manager.py {action} failed: {exc}", exc_info=True)
        _output({"success": False, "error": str(exc)})
        sys.exit(1)


if __name__ == "__main__":
    main()
