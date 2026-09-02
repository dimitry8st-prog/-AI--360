"""OpenAI-compatible chat completions. Used from stage 3; stage 1 only wires the client."""

import json
from typing import Any

import httpx

from app.ai.providers.base import LLMProvider
from app.core.config import Settings
from app.core.exceptions import AIUnavailableError


class OpenAICompatProvider(LLMProvider):
    name = "openai_compat"

    def __init__(self, settings: Settings):
        self._settings = settings

    @property
    def available(self) -> bool:
        return self._settings.llm_is_live

    async def complete_json(self, *, system: str, user: str, temperature: float) -> dict[str, Any]:
        if not self.available:
            raise AIUnavailableError()
        payload = {
            "model": self._settings.llm_model,
            "temperature": temperature,
            "max_tokens": self._settings.llm_max_tokens,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self._settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        url = self._settings.llm_base_url.rstrip("/") + "/chat/completions"
        try:
            async with httpx.AsyncClient(timeout=self._settings.llm_timeout) as client:
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                return json.loads(content)
        except (httpx.HTTPError, KeyError, json.JSONDecodeError) as exc:
            raise AIUnavailableError() from exc
