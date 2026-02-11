"""General application settings"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Discord configuration
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
COMMAND_PREFIX = '!'

# Docker configuration
DOCKER_NETWORK = os.getenv('DOCKER_NETWORK', 'ctf-isolated')
CONTAINER_SUBNET = os.getenv('CONTAINER_SUBNET', '172.20.0.0/16')

# Lab configuration
MAX_LABS_PER_USER = int(os.getenv('MAX_LABS_PER_USER', 3))
AUTO_CLEANUP_HOURS = int(os.getenv('AUTO_CLEANUP_HOURS', 4))

# Rate limiting
RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 10))

# AI configuration (optional)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
AI_MODEL = "deepseek/deepseek-chat"

# Paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
LOG_DIR = BASE_DIR / "logs"
CHALLENGES_DIR = BASE_DIR / "challenges"

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)
CHALLENGES_DIR.mkdir(exist_ok=True)

# Logging
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = LOG_DIR / os.getenv('LOG_FILE', 'bagley.log')

# Available lab types
AVAILABLE_LABS = {
    "dvwa": {
        "name": "Damn Vulnerable Web Application",
        "image": "vulnerables/web-dvwa",
        "category": "web",
        "difficulty": "beginner",
        "description": "Practice SQL injection, XSS, command injection",
        "port": 80,
    },
    "webgoat": {
        "name": "WebGoat",
        "image": "webgoat/webgoat:latest",
        "category": "web",
        "difficulty": "beginner",
        "description": "OWASP Top 10 practice environment",
        "port": 8080,
    },
    "juice-shop": {
        "name": "OWASP Juice Shop",
        "image": "bkimminich/juice-shop",
        "category": "web",
        "difficulty": "beginner",
        "description": "Modern web app vulnerabilities",
        "port": 3000,
    },
    "metasploitable": {
        "name": "Metasploitable 2",
        "image": "tleemcjr/metasploitable2",
        "category": "system",
        "difficulty": "intermediate",
        "description": "Full penetration testing environment",
        "port": 22,
    },
}
