from __future__ import annotations

import logging

import httpx

from ...application.ports.llm_port import LLMPort, MensajeLLM

log = logging.getLogger("ollama_adapter")


class OllamaAdapter(LLMPort):
    """Adapter sobre /api/chat de Ollama. SRP: hablar HTTP con Ollama."""

    KEEP_ALIVE = "24h"
    NUM_CTX = 8192

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
            "keep_alive": self.KEEP_ALIVE,
            "options": {"temperature": 0.2, "num_ctx": self.NUM_CTX},
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

    async def warmup(self) -> None:
        """Carga el modelo a VRAM con `num_ctx` final para evitar cold-load en el primer /chat."""
        payload = {
            "model": self._model,
            "messages": [{"role": "user", "content": "ok"}],
            "stream": False,
            "keep_alive": self.KEEP_ALIVE,
            "options": {"num_ctx": self.NUM_CTX},
        }
        try:
            async with httpx.AsyncClient(timeout=self._timeout) as client:
                r = await client.post(f"{self._host}/api/chat", json=payload)
                r.raise_for_status()
            log.info("ollama warmup ok: model=%s", self._model)
        except Exception as exc:
            log.warning("ollama warmup fallo (seguimos igual): %s", exc)
