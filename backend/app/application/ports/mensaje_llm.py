from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class MensajeLLM:
    """DTO de un mensaje intercambiado con el LLM."""

    role: str
    content: str = ""
    tool_calls: list[dict] | None = None

    def to_dict(self) -> dict[str, Any]:
        base: dict[str, Any] = {"role": self.role, "content": self.content}
        if self.tool_calls:
            base["tool_calls"] = self.tool_calls
        return base
