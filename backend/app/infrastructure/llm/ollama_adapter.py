from __future__ import annotations

import asyncio
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
    - asyncio.Semaphore(max_parallel): backpressure en Python antes de llegar
      a Ollama. Sin esto 50 usuarios simultáneos abren 50 conexiones pero
      Ollama solo procesa max_parallel a la vez; los 44 restantes cuelgan
      consumiendo memoria hasta timeout. Con el semáforo quedan en la cola
      de asyncio (cero RAM de conexión) y se atienden ordenadamente.
    - num_ctx=6144 en lugar de 8192: el asistente envía max 10 mensajes de
      historial + system prompt (~2000 tokens) + bloques de contexto (~400).
      6144 cubre el peor caso con margen y ahorra ~180MB de KV-cache VRAM
      por slot, permitiendo subir max_parallel a 6 en la RTX 5090.
    - Timeout extendido: 180s — tool calls con LLM pueden tardar 30-90s en
      concurrencia, no queremos cortar."""

    KEEP_ALIVE = "24h"
    # 6144 = system(~2k) + historial×10(~2k) + bloques+contexto(~400) + output(~1500).
    # Reducido de 8192: ahorra ~180MB KV-VRAM/slot → permite NUM_PARALLEL=6 en RTX 5090.
    NUM_CTX = 6144

    def __init__(
        self,
        host: str,
        model: str,
        timeout: float = 180.0,
        max_parallel: int = 6,
    ) -> None:
        self._host = host
        self._model = model
        self._timeout = timeout
        self._cliente: Optional[httpx.AsyncClient] = None
        # Backpressure: cola en Python en lugar de saturar Ollama.
        # max_parallel debe coincidir con OLLAMA_NUM_PARALLEL en docker-compose.
        self._semaphore = asyncio.Semaphore(max_parallel)

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
        async with self._semaphore:
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
            async with self._semaphore:
                client = self._client()
                r = await client.post(f"{self._host}/api/chat", json=payload)
            r.raise_for_status()
            log.info("ollama warmup ok: model=%s", self._model)
        except Exception as exc:
            log.warning("ollama warmup fallo (seguimos igual): %s", exc)
