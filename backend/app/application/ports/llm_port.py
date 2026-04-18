from __future__ import annotations

from abc import ABC, abstractmethod

from .mensaje_llm import MensajeLLM


class LLMPort(ABC):
    """Puerto de salida hacia un modelo de lenguaje con tool calling."""

    @abstractmethod
    async def chat(self, mensajes: list[dict], tools: list[dict]) -> MensajeLLM: ...
