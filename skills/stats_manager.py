"""User statistics and leaderboard management"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from config.settings import DATA_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class StatsManager:
    """Manages user statistics and points"""

    def __init__(self):
        self.stats_file = DATA_DIR / "user_stats.json"
        self.stats: Dict[str, dict] = {}
        self._load_stats()

    def _load_stats(self):
        """Load stats from JSON file"""
        if self.stats_file.exists():
            try:
                with open(self.stats_file, 'r') as f:
                    self.stats = json.load(f)
                logger.info(f"Loaded stats for {len(self.stats)} users")
            except json.JSONDecodeError as e:
                logger.error(f"Error loading stats: {e}")
                self.stats = {}
        else:
            self.stats = {}

    def _save_stats(self):
        """Save stats to JSON file"""
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving stats: {e}")

    def _ensure_user(self, username: str):
        """Ensure user exists in stats"""
        if username not in self.stats:
            self.stats[username] = {
                "total_points": 0,
                "solves": [],
                "categories": {},
                "labs_started": 0,
                "first_seen": datetime.now().isoformat(),
            }

    def record_solve(self, username: str, challenge_id: str, points: int, category: str) -> bool:
        """Record a successful challenge solve"""
        self._ensure_user(username)

        # Check if already solved
        solved_ids = [s['challenge_id'] for s in self.stats[username]['solves']]
        if challenge_id in solved_ids:
            return False  # Already solved

        # Add points
        self.stats[username]['total_points'] += points

        # Record solve
        self.stats[username]['solves'].append({
            "challenge_id": challenge_id,
            "points": points,
            "category": category,
            "timestamp": datetime.now().isoformat()
        })

        # Update category stats
        if category not in self.stats[username]['categories']:
            self.stats[username]['categories'][category] = 0
        self.stats[username]['categories'][category] += points

        self._save_stats()
        logger.info(f"Recorded solve: {username} - {challenge_id} (+{points} pts)")
        return True

    def record_lab_start(self, username: str):
        """Record that user started a lab"""
        self._ensure_user(username)
        self.stats[username]['labs_started'] += 1
        self._save_stats()

    def get_leaderboard(self, limit: int = 10) -> List[Tuple[str, dict]]:
        """Get top players by points"""
        sorted_users = sorted(
            self.stats.items(),
            key=lambda x: x[1]['total_points'],
            reverse=True
        )
        return sorted_users[:limit]

    def get_user_stats(self, username: str) -> Optional[dict]:
        """Get stats for a specific user"""
        return self.stats.get(username)

    def format_leaderboard(self, limit: int = 10) -> str:
        """Format leaderboard for Discord"""
        leaders = self.get_leaderboard(limit)

        if not leaders:
            return "📊 No stats yet. Be the first to solve a challenge!"

        msg = "🏆 **Top Players**\n\n"

        medals = ["👑", "🥈", "🥉"]

        for i, (username, data) in enumerate(leaders, 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            points = data['total_points']
            solves = len(data['solves'])

            msg += f"{medal} **{username}** - {points} pts ({solves} solves)\n"

        return msg

    def format_user_stats(self, username: str) -> str:
        """Format user stats for Discord"""
        data = self.get_user_stats(username)

        if not data:
            return f"📊 No stats for {username}. Start solving challenges!"

        msg = f"📊 **{username}'s Stats**\n\n"
        msg += f"**Total Points:** {data['total_points']}\n"
        msg += f"**Challenges Solved:** {len(data['solves'])}\n"
        msg += f"**Labs Started:** {data.get('labs_started', 0)}\n\n"

        if data['categories']:
            msg += "**By Category:**\n"
            for cat, pts in sorted(data['categories'].items(), key=lambda x: x[1], reverse=True):
                msg += f"  • {cat}: {pts} pts\n"

        return msg
