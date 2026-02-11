"""Challenge management system"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional
from config.settings import CHALLENGES_DIR

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ChallengeManager:
    """Manages CTF challenges"""

    def __init__(self):
        self.challenges_dir = CHALLENGES_DIR
        self.challenges: Dict[str, dict] = {}
        self._load_all_challenges()

    def _load_all_challenges(self):
        """Load all challenge files from challenges directory"""

        if not self.challenges_dir.exists():
            logger.warning(f"Challenges directory not found: {self.challenges_dir}")
            return

        # Iterate through category directories
        for category_dir in self.challenges_dir.iterdir():
            if not category_dir.is_dir():
                continue

            # Load all JSON files in category
            for challenge_file in category_dir.glob("*.json"):
                try:
                    with open(challenge_file, 'r') as f:
                        challenge = json.load(f)
                        challenge_id = challenge.get('id')

                        if not challenge_id:
                            logger.warning(f"Challenge missing ID: {challenge_file}")
                            continue

                        self.challenges[challenge_id] = challenge
                        logger.info(f"Loaded challenge: {challenge_id}")

                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in {challenge_file}: {e}")
                except Exception as e:
                    logger.error(f"Error loading {challenge_file}: {e}")

        logger.info(f"Loaded {len(self.challenges)} challenges across {len(self.list_categories())} categories")

    def list_categories(self) -> List[str]:
        """Get list of all challenge categories"""
        categories = set(c.get('category', 'uncategorized') for c in self.challenges.values())
        return sorted(list(categories))

    def get_challenges_by_category(self, category: str) -> List[dict]:
        """Get all challenges in a specific category"""
        return [
            c for c in self.challenges.values()
            if c.get('category', '').lower() == category.lower()
        ]

    def get_challenge(self, challenge_id: str) -> Optional[dict]:
        """Get a specific challenge by ID"""
        return self.challenges.get(challenge_id)

    def check_flag(self, challenge_id: str, submitted_flag: str) -> bool:
        """Verify if submitted flag is correct"""
        challenge = self.get_challenge(challenge_id)

        if not challenge:
            logger.warning(f"Challenge not found: {challenge_id}")
            return False

        correct_flag = challenge.get('flag', '')
        return submitted_flag.strip() == correct_flag

    def get_hint(self, challenge_id: str, hint_number: int = 0) -> Optional[str]:
        """Get a hint for a challenge"""
        challenge = self.get_challenge(challenge_id)

        if not challenge:
            return None

        hints = challenge.get('hints', [])

        if hint_number >= len(hints):
            return None

        return hints[hint_number]

    def format_challenge_list(self, category: str) -> str:
        """Format challenges for Discord display"""
        challenges = self.get_challenges_by_category(category)

        if not challenges:
            return f"❌ No challenges found in category: {category}"

        # Sort by points
        challenges.sort(key=lambda c: c.get('points', 0))

        msg = f"🔐 **{category.title()} Challenges:**\n\n"

        for c in challenges:
            difficulty_emoji = {
                'easy': '🟢',
                'medium': '🟡',
                'hard': '🔴'
            }.get(c.get('difficulty', 'medium'), '⚪')

            msg += (
                f"{difficulty_emoji} **{c.get('title')}** "
                f"({c.get('points', 0)} pts)\n"
                f"   ID: `{c.get('id')}`\n"
            )

        msg += f"\nSolve: `!solve <id> <flag>`"
        return msg
