from __future__ import annotations

import logging
from typing import Optional

import httpx

from ...application.ports.llm_port import LLMPort, MensajeLLM

log = logging.getLogger("groq_adapter")

_GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


class GroqAdapter(LLMPort):
    """Adapter para Groq API (OpenAI-compatible). SRP: hablar HTTP con Groq.

    Groq implementa la interfaz OpenAI: misma estructura de messages, tools y
    tool_calls. La diferencia vs Ollama: arguments llega como JSON string (no
    dict) pero ValueParser.parse_args() ya lo normaliza aguas abajo."""

    def __init__(self, api_key: str, model: str, timeout: float = 60.0) -> None:
        self._api_key = api_key
        self._model = model
        self._timeout = timeout
        self._cliente: Optional[httpx.AsyncClient] = None

    def _client(self) -> httpx.AsyncClient:
        if self._cliente is None or self._cliente.is_closed:
            self._cliente = httpx.AsyncClient(
                timeout=self._timeout,
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                limits=httpx.Limits(max_connections=20, max_keepalive_connections=10),
            )
        return self._cliente

    async def cerrar(self) -> None:
        if self._cliente is not None and not self._cliente.is_closed:
            await self._cliente.aclose()
            self._cliente = None

    async def warmup(self) -> None:
        """No-op: Groq no requiere precarga de modelo en VRAM."""

    async def chat(self, mensajes: list[dict], tools: list[dict]) -> MensajeLLM:
        payload: dict = {
            "model": self._model,
            "messages": mensajes,
            "temperature": 0.2,
        }
        if tools:
            payload["tools"] = [
                {"type": "function", "function": t} for t in tools
            ]
            payload["tool_choice"] = "auto"

        r = await self._client().post(_GROQ_API_URL, json=payload)
        r.raise_for_status()
        data = r.json()

        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}

        # OpenAI tool_calls: [{"id":..,"type":"function","function":{"name":..,"arguments":"..json_str.."}}]
        # Normalizamos a formato interno idéntico al de Ollama.
        raw_tc = msg.get("tool_calls")
        tool_calls = None
        if raw_tc:
            tool_calls = [
                {"function": {"name": tc["function"]["name"], "arguments": tc["function"]["arguments"]}}
                for tc in raw_tc
            ]

        return MensajeLLM(
            role=msg.get("role", "assistant"),
            content=msg.get("content") or "",
            tool_calls=tool_calls,
        )
