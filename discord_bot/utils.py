"""Utility functions for Discord bot"""

import logging
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiting for bot commands"""

    def __init__(self, soft_limit: int = 10, warn_limit: int = 15, hard_limit: int = 20):
        self.soft_limit = soft_limit
        self.warn_limit = warn_limit
        self.hard_limit = hard_limit

        self.user_requests = defaultdict(list)
        self.warned_users = set()

    def check_limit(self, username: str) -> Tuple[bool, Optional[str]]:
        """
        Check if user is within rate limits

        Returns:
            (allowed, optional_warning_message)
        """
        now = datetime.now()
        cutoff = now - timedelta(minutes=1)

        # Clean old requests
        self.user_requests[username] = [
            t for t in self.user_requests[username]
            if t > cutoff
        ]

        request_count = len(self.user_requests[username])

        # Soft limit - no warning
        if request_count < self.soft_limit:
            self.user_requests[username].append(now)
            return True, None

        # Warn limit - show warning once
        elif request_count < self.warn_limit:
            self.user_requests[username].append(now)

            if username not in self.warned_users:
                self.warned_users.add(username)
                return True, "⚠️ You're sending commands quickly. Please slow down."

            return True, None

        # Hard limit - block
        elif request_count < self.hard_limit:
            self.user_requests[username].append(now)
            return True, None

        else:
            logger.warning(f"RATE_LIMIT_EXCEEDED - User: {username} - Count: {request_count}")
            return False, "❌ Too many commands. Wait 1 minute."

    def reset_warnings(self, username: str):
        """Reset warnings for a user (called periodically)"""
        if username in self.warned_users:
            self.warned_users.remove(username)


# Global rate limiter instance
rate_limiter = RateLimiter()
