from __future__ import annotations

import logging
from typing import Optional

import httpx

from ...application.ports.llm_port import LLMPort, MensajeLLM

log = logging.getLogger("ollama_adapter")


class OllamaAdapter(LLMPort):
    """Adapter sobre /api/chat de Ollama. SRP: hablar HTTP con Ollama.

    Optimizaciones de concurrencia:
    - Cliente httpx singleton lazy: reutiliza pool de conexiones TCP entre
      requests. Sin esto cada chat() abría/cerraba conexión (overhead 50-150ms).
    - Connection limits altos: hasta 20 conexiones simultáneas al daemon.
      Combinado con OLLAMA_NUM_PARALLEL=4 en docker-compose, soporta 4
      generaciones paralelas con margen para warmup/health.
    - Timeout extendido: 180s (era OK pero ahora es explícito) — tool calls
      con LLM pueden tardar 30-90s en concurrencia, no queremos cortar."""

    KEEP_ALIVE = "24h"
    NUM_CTX = 8192

    def __init__(self, host: str, model: str, timeout: float = 180.0) -> None:
        self._host = host
        self._model = model
        self._timeout = timeout
        self._cliente: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        """Cliente singleton con connection pool. Se crea lazy en el primer
        uso (no podemos hacerlo sync en __init__ porque httpx.AsyncClient
        requiere event loop)."""
        if self._cliente is None or self._cliente.is_closed:
            self._cliente = httpx.AsyncClient(
                timeout=self._timeout,
                limits=httpx.Limits(
                    max_connections=20,
                    max_keepalive_connections=10,
                    keepalive_expiry=60.0,
                ),
                http2=False,  # ollama no implementa h2; h1 con keepalive es óptimo
            )
        return self._cliente

    async def cerrar(self) -> None:
        """Cierra el pool de conexiones — usar en shutdown."""
        if self._cliente is not None and not self._cliente.is_closed:
            await self._cliente.aclose()
            self._cliente = None

    async def chat(self, mensajes: list[dict], tools: list[dict]) -> MensajeLLM:
        payload = {
            "model": self._model,
            "messages": mensajes,
            "tools": tools,
            "stream": False,
            "keep_alive": self.KEEP_ALIVE,
            "options": {"temperature": 0.2, "num_ctx": self.NUM_CTX},
        }
        client = self._client()
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
            client = self._client()
            r = await client.post(f"{self._host}/api/chat", json=payload)
            r.raise_for_status()
            log.info("ollama warmup ok: model=%s", self._model)
        except Exception as exc:
            log.warning("ollama warmup fallo (seguimos igual): %s", exc)
