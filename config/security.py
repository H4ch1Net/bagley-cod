"""Security configurations and validation"""

import re
import logging
from typing import Tuple

# Docker security options
DOCKER_SECURITY_OPTS = [
    "--security-opt=no-new-privileges",
    "--cap-drop=ALL",
    "--cap-add=NET_BIND_SERVICE",
    "--read-only",
    "--tmpfs=/tmp:rw,noexec,nosuid",
]

RESOURCE_LIMITS = {
    "memory": "2g",
    "cpus": "1",
    "pids_limit": 100,
}

# Blocked input patterns (regex)
BLOCKED_PATTERNS = [
    r'\$\(',           # Command substitution
    r'`[^`]+`',        # Backtick execution
    r'&&|\|\|',        # Command chaining
    r';.*rm',          # Destructive commands
    r'curl|wget',      # External fetching
    r'eval|exec',      # Code execution
    r'import\s+os',    # OS module access
    r'http://|https://',  # URL schemes
]

# Discord role requirements
ALLOWED_ROLES = ["verified-member", "officers", "admin"]


def sanitize_input(user_input: str) -> Tuple[bool, str]:
    """
    Validate and sanitize user input

    Args:
        user_input: Raw user input string

    Returns:
        Tuple of (is_valid, cleaned_input or error_message)
    """
    # Check for malicious patterns
    for pattern in BLOCKED_PATTERNS:
        if re.search(pattern, user_input, re.IGNORECASE):
            logging.warning(f"BLOCKED_INPUT - Pattern: {pattern} - Input: {user_input[:50]}")
            return False, "Invalid input detected"

    # Clean and return
    cleaned = user_input.strip()
    return True, cleaned


def check_role(user_roles: list) -> bool:
    """Check if user has required role"""
    return any(role in ALLOWED_ROLES for role in user_roles)
