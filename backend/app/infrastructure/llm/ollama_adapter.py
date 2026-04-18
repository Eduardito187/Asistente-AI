from __future__ import annotations

import httpx

from ...application.ports.llm_port import LLMPort, MensajeLLM


class OllamaAdapter(LLMPort):
    """Adapter sobre /api/chat de Ollama. SRP: hablar HTTP con Ollama."""

    def __init__(self, host: str, model: str, timeout: float = 180.0) -> None:
        self._host = host
        self._model = model
        self._timeout = timeout

    async def chat(self, mensajes: list[dict], tools: list[dict]) -> MensajeLLM:
        payload = {
            "model": self._model,
            "messages": mensajes,
            "tools": tools,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 8192},
        }
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.post(f"{self._host}/api/chat", json=payload)
            r.raise_for_status()
            data = r.json()
        msg = data.get("message") or {}
        return MensajeLLM(
            role=msg.get("role", "assistant"),
            content=msg.get("content") or "",
            tool_calls=msg.get("tool_calls") or None,
        )
