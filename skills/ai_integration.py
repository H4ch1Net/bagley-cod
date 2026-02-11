"""OpenRouter API integration for natural language parsing"""

import os
import json
import logging
import requests
from typing import Dict, Optional
from config.settings import OPENROUTER_API_KEY, AI_MODEL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIOrchestrator:
    """Natural language command parsing via OpenRouter"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or OPENROUTER_API_KEY
        self.endpoint = "https://openrouter.ai/api/v1/chat/completions"
        self.model = AI_MODEL

        self.system_prompt = """You are a CTF lab assistant. Parse user commands and return JSON.

Available actions: start, stop, delete, status, list, help
Available labs: dvwa, webgoat, juice-shop, metasploitable

Return JSON format:
{
  "action": "start|stop|delete|status|list|help",
  "lab_type": "dvwa|webgoat|juice-shop|metasploitable",
  "success": true
}

Examples:
"start dvwa" -> {"action": "start", "lab_type": "dvwa", "success": true}
"I need a webgoat lab" -> {"action": "start", "lab_type": "webgoat", "success": true}
"stop my juice shop" -> {"action": "stop", "lab_type": "juice-shop", "success": true}
"what's running?" -> {"action": "status", "success": true}
"list available labs" -> {"action": "list", "success": true}

Only return valid JSON. No explanations."""

    def parse_command(self, user_input: str) -> Dict:
        """Parse natural language command"""

        if not self.api_key:
            logger.warning("No OpenRouter API key configured")
            return {"error": "AI parsing not available"}

        try:
            response = requests.post(
                self.endpoint,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": user_input}
                    ],
                },
                timeout=30
            )

            response.raise_for_status()
            data = response.json()

            # Extract response
            content = data.get('choices', [{}])[0].get('message', {}).get('content', '')

            # Clean markdown code blocks if present
            content = content.strip()
            if content.startswith('```json'):
                content = content[7:]
            if content.startswith('```'):
                content = content[3:]
            if content.endswith('```'):
                content = content[:-3]
            content = content.strip()

            # Parse JSON
            result = json.loads(content)
            return result

        except requests.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"error": "AI service unavailable"}
        except json.JSONDecodeError as e:
            logger.error(f"JSON parse error: {e} - Content: {content}")
            return {"error": "Invalid response from AI"}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {"error": "Internal error"}
