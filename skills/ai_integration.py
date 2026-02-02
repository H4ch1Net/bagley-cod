import json
import os
import re
from typing import Any, Dict, Optional

import requests


class AIOrchestrator:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        self.model = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct")
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://localhost",
            "X-Title": "Bagley",
        }

    def _clean_json(self, content: str) -> str:
        content = content.strip()
        content = re.sub(r"^```(?:json)?", "", content, flags=re.IGNORECASE).strip()
        content = re.sub(r"```$", "", content).strip()
        return content

    def parse_command(self, user_input: str, username: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "AI is disabled (no API key)"}

        system_prompt = (
            "You are a command parser for a lab orchestrator. "
            "Return ONLY valid JSON with keys: action, lab_type. "
            "Valid actions: start, stop, delete, status, list, help. "
            "Valid lab types: dvwa, webgoat, metasploitable, juice-shop. "
            "If no lab type is mentioned, use null."
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"User: {username}\nCommand: {user_input}",
                },
            ],
            "temperature": 0.3,
            "max_tokens": 200,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            cleaned = self._clean_json(content)
            parsed = json.loads(cleaned)
            return {"success": True, "command": parsed}
        except requests.RequestException as exc:
            return {"success": False, "error": f"Request failed: {exc}"}
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            return {"success": False, "error": f"Invalid AI response: {exc}"}

    def get_help_response(self, topic: Optional[str] = None) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "AI is disabled (no API key)"}

        prompt = "Provide a concise help response for the Bagley CLI."
        if topic:
            prompt = f"Explain how to use '{topic}' in Bagley CLI."

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 300,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {"success": True, "response": content.strip()}
        except requests.RequestException as exc:
            return {"success": False, "error": f"Request failed: {exc}"}
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            return {"success": False, "error": f"Invalid AI response: {exc}"}

    def explain_lab(self, lab_type: str) -> Dict[str, Any]:
        if not self.api_key:
            return {"success": False, "error": "AI is disabled (no API key)"}

        prompt = (
            "Explain what this lab type is used for and mention common vulnerabilities: "
            f"{lab_type}"
        )

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are a cybersecurity tutor."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 300,
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self._headers(),
                json=payload,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return {"success": True, "response": content.strip()}
        except requests.RequestException as exc:
            return {"success": False, "error": f"Request failed: {exc}"}
        except (KeyError, IndexError, json.JSONDecodeError) as exc:
            return {"success": False, "error": f"Invalid AI response: {exc}"}
