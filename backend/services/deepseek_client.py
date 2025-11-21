"""Thin HTTP client for interacting with DeepSeek Cloud API."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

import httpx

from backend import config

logger = logging.getLogger(__name__)


class DeepSeekClient:
    """Helper around DeepSeek REST API (chat + speech)."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        chat_model: Optional[str] = None,
        transcribe_model: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or config.DEEPSEEK_API_KEY
        if not self.api_key:
            raise RuntimeError(
                "DEEPSEEK_API_KEY is not configured. "
                "Set it in your environment or .env file to call the cloud models."
            )

        self.base_url = base_url or config.DEEPSEEK_BASE_URL
        self.chat_model = chat_model or config.DEEPSEEK_CHAT_MODEL
        self.transcribe_model = transcribe_model or config.DEEPSEEK_TRANSCRIBE_MODEL
        self.timeout = timeout or config.DEEPSEEK_TIMEOUT

        self._http = httpx.Client(base_url=self.base_url, timeout=self.timeout)
        self._json_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict] = None,
    ) -> str:
        """Call the DeepSeek chat-completions endpoint."""
        payload: Dict = {
            "model": self.chat_model,
            "messages": messages,
            "temperature": temperature,
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens
        if response_format:
            payload["response_format"] = response_format

        logger.debug("DeepSeek chat payload: %s", payload)
        resp = self._http.post("/chat/completions", headers=self._json_headers, json=payload)
        resp.raise_for_status()
        data = resp.json()
        try:
            return data["choices"][0]["message"]["content"]
        except (KeyError, IndexError) as exc:
            raise RuntimeError(f"Unexpected DeepSeek response: {data}") from exc

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        *,
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> Dict:
        """Call chat() and parse the answer as JSON."""
        content = self.chat(messages, temperature=temperature, max_tokens=max_tokens)
        content = content.strip()

        # Strip accidental markdown fencing
        if "```" in content:
            parts = content.split("```")
            # Look for block that parses as JSON
            for part in parts:
                candidate = part.strip()
                if not candidate:
                    continue
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(content)
        except json.JSONDecodeError as exc:
            logger.warning("Failed to parse DeepSeek JSON response: %s", content)
            raise

    def transcribe(
        self,
        audio_path: str | Path,
        *,
        language: Optional[str] = None,
        temperature: float = 0.0,
    ) -> Dict:
        """Send audio file to DeepSeek speech-to-text endpoint."""
        audio_path = str(audio_path)
        path_obj = Path(audio_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        data = {
            "model": self.transcribe_model,
            "temperature": temperature,
            "response_format": "verbose_json",
        }
        if language:
            data["language"] = language

        headers = {"Authorization": f"Bearer {self.api_key}"}

        with path_obj.open("rb") as file_obj:
            files = {
                "file": (path_obj.name, file_obj, "audio/wav"),
            }

            resp = self._http.post(
                "/audio/transcriptions",
                data=data,
                headers=headers,
                files=files,
            )
        resp.raise_for_status()
        return resp.json()

    def close(self):
        """Close the underlying HTTP client."""
        self._http.close()

    def __del__(self):
        try:
            self.close()
        except Exception:  # pragma: no cover - best effort
            pass


