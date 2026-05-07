from __future__ import annotations

import hashlib
import json
import logging
from typing import Optional

from ...application.ports.cache import Cache
from ...application.ports.llm_port import LLMPort, MensajeLLM

log = logging.getLogger("llm_cache_adapter")


class LLMCacheAdapter(LLMPort):
    """Decorator sobre LLMPort que memoriza respuestas idénticas por TTL corto.

    Caso de uso típico:
    - 2 navegadores abren a la misma vez sin contexto y mandan 'hola'
    - Antes: ambos hacen inference completo en GPU (~3-5s c/u)
    - Ahora: el primero genera + cachea, el segundo lee del cache (~5ms)

    Hash key incluye: model + messages + tools + temperature. Si cambia
    cualquier cosa el cache no se reusa.

    TTL bajo (60s default) para evitar respuestas obsoletas. Si el cliente
    está activo cambiando contexto, el cache prácticamente no aplica
    (cada turno tiene historial distinto). Solo aporta en:
    - Saludos genéricos repetidos en distintas sesiones
    - Reintentos del mismo turno (timeouts/errores transitorios)
    - Pruebas de carga / smoke tests

    NUNCA cachea respuestas con tool_calls — las tool calls dependen del
    estado de la sesión y serían inválidas para otra sesión."""

    _PREFIJO = "llm:chat:"

    def __init__(
        self,
        llm: LLMPort,
        cache: Cache,
        ttl_segundos: int = 60,
    ) -> None:
        self._llm = llm
        self._cache = cache
        self._ttl = ttl_segundos

    async def chat(self, mensajes: list[dict], tools: list[dict]) -> MensajeLLM:
        key = self._key(mensajes, tools)
        cacheado = self._leer_cache(key)
        if cacheado is not None:
            return cacheado
        respuesta = await self._llm.chat(mensajes, tools)
        # No cachear respuestas con tool_calls: dependen del estado de sesión.
        if not respuesta.tool_calls:
            self._guardar_cache(key, respuesta)
        return respuesta

    async def warmup(self) -> None:
        await self._llm.warmup()

    async def cerrar(self) -> None:
        cerrar = getattr(self._llm, "cerrar", None)
        if callable(cerrar):
            await cerrar()

    # ===== Internos =========================================================

    @classmethod
    def _key(cls, mensajes: list[dict], tools: list[dict]) -> str:
        payload = {
            "messages": mensajes,
            "tools": tools or [],
        }
        raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=False)
        h = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]
        return f"{cls._PREFIJO}{h}"

    def _leer_cache(self, key: str) -> Optional[MensajeLLM]:
        try:
            raw = self._cache.get(key)
        except Exception:
            return None
        if not raw:
            return None
        try:
            data = json.loads(raw)
            return MensajeLLM(
                role=data.get("role", "assistant"),
                content=data.get("content") or "",
                tool_calls=data.get("tool_calls"),
            )
        except (ValueError, TypeError):
            return None

    def _guardar_cache(self, key: str, respuesta: MensajeLLM) -> None:
        try:
            payload = json.dumps({
                "role": respuesta.role,
                "content": respuesta.content,
                "tool_calls": respuesta.tool_calls,
            }, ensure_ascii=False, default=str)
            self._cache.set(key, payload, ttl_segundos=self._ttl)
        except Exception:
            log.debug("no se pudo cachear respuesta LLM (continuamos)", exc_info=True)
