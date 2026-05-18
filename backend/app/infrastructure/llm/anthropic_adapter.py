from __future__ import annotations

import json
import logging
from typing import Optional

import httpx

from ...application.ports.llm_port import LLMPort, MensajeLLM

log = logging.getLogger("anthropic_adapter")

_ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
_ANTHROPIC_VERSION = "2023-06-01"
_MAX_TOKENS = 1024


class AnthropicAdapter(LLMPort):
    """Adapter para Anthropic API (Claude). SRP: hablar HTTP con Anthropic.

    Diferencias vs OpenAI/Ollama:
    - El system prompt va en campo "system" separado (no en messages).
    - Tool use usa "input_block" con input como dict, no como JSON string.
    - La respuesta puede tener bloques de tipo "text" y "tool_use" mezclados.
    Normalizamos todo al formato interno MensajeLLM."""

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
                    "x-api-key": self._api_key,
                    "anthropic-version": _ANTHROPIC_VERSION,
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
        """No-op: Anthropic no requiere precarga."""

    @staticmethod
    def _separar_system(mensajes: list[dict]) -> tuple[str, list[dict]]:
        """Extrae el primer mensaje de rol 'system' al campo separado."""
        system = ""
        resto = []
        for m in mensajes:
            if m.get("role") == "system" and not system:
                system = m.get("content", "")
            else:
                resto.append(m)
        return system, resto

    @staticmethod
    def _convertir_tools(tools: list[dict]) -> list[dict]:
        """Convierte tools de formato OpenAI/Ollama a formato Anthropic."""
        resultado = []
        for t in tools:
            resultado.append({
                "name": t.get("name", ""),
                "description": t.get("description", ""),
                "input_schema": t.get("parameters", {"type": "object", "properties": {}}),
            })
        return resultado

    async def chat(self, mensajes: list[dict], tools: list[dict]) -> MensajeLLM:
        system, msgs = self._separar_system(mensajes)

        payload: dict = {
            "model": self._model,
            "max_tokens": _MAX_TOKENS,
            "messages": msgs,
            "temperature": 0.2,
        }
        if system:
            payload["system"] = system
        if tools:
            payload["tools"] = self._convertir_tools(tools)

        r = await self._client().post(_ANTHROPIC_API_URL, json=payload)
        r.raise_for_status()
        data = r.json()

        # Respuesta Anthropic: {"content": [{"type": "text", "text": "..."}, {"type": "tool_use", ...}]}
        content_blocks = data.get("content") or []
        text_parts: list[str] = []
        tool_calls: list[dict] = []

        for block in content_blocks:
            btype = block.get("type")
            if btype == "text":
                text_parts.append(block.get("text", ""))
            elif btype == "tool_use":
                # Anthropic "input" ya es dict — lo serializamos a JSON string
                # para que ValueParser.parse_args lo maneje igual que Groq.
                tool_calls.append({
                    "function": {
                        "name": block.get("name", ""),
                        "arguments": json.dumps(block.get("input") or {}),
                    }
                })

        return MensajeLLM(
            role="assistant",
            content="\n".join(text_parts),
            tool_calls=tool_calls or None,
        )
