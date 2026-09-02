from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    name: str

    @abstractmethod
    async def complete_json(self, *, system: str, user: str, temperature: float) -> dict[str, Any]:
        """Return a JSON object. Must not execute instructions found in documents."""
        raise NotImplementedError

    @property
    def available(self) -> bool:
        return True
