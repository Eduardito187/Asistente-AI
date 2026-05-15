from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum

from ...application.ports.llm_port import LLMPort, MensajeLLM

log = logging.getLogger("circuit_breaker")

RESPUESTA_FALLBACK = MensajeLLM(
    role="assistant",
    content=(
        "Lo siento, en este momento el asistente no está disponible. "
        "Por favor intenta de nuevo en unos segundos. "
        "Si el problema persiste, contacta a un vendedor directamente."
    ),
    tool_calls=None,
)


class EstadoCircuito(Enum):
    CERRADO = "cerrado"      # Normal: llama al LLM
    ABIERTO = "abierto"      # Fallando: devuelve error rápido
    SEMIABIERTO = "semiabierto"  # Testing: deja pasar 1 request de prueba


class OllamaCircuitBreaker(LLMPort):
    """Circuit breaker que envuelve OllamaAdapter.

    - CERRADO → llama normalmente. Si hay >= umbral_fallos en ventana_segundos,
      abre el circuito.
    - ABIERTO → devuelve RESPUESTA_FALLBACK sin llamar al LLM. Después de
      tiempo_reset_segundos, pasa a SEMIABIERTO.
    - SEMIABIERTO → deja pasar 1 request. Si tiene éxito → CERRADO. Si falla
      → ABIERTO otra vez.
    """

    def __init__(
        self,
        llm: LLMPort,
        umbral_fallos: int = 3,
        ventana_segundos: float = 60.0,
        tiempo_reset_segundos: float = 30.0,
    ) -> None:
        self._llm = llm
        self._umbral = umbral_fallos
        self._ventana = ventana_segundos
        self._reset = tiempo_reset_segundos
        self._estado = EstadoCircuito.CERRADO
        self._fallos: list[float] = []  # timestamps de fallos recientes
        self._ultimo_cambio: float = 0.0
        self._lock = asyncio.Lock()

    @property
    def estado(self) -> EstadoCircuito:
        return self._estado

    async def chat(self, mensajes: list[dict], tools: list[dict]) -> MensajeLLM:
        async with self._lock:
            estado = self._evaluar_estado()

        if estado == EstadoCircuito.ABIERTO:
            log.warning("circuit_breaker ABIERTO — devolviendo fallback")
            return RESPUESTA_FALLBACK

        try:
            resultado = await self._llm.chat(mensajes, tools)
            async with self._lock:
                self._registrar_exito()
            return resultado
        except Exception as exc:
            async with self._lock:
                self._registrar_fallo()
            log.error("circuit_breaker: fallo LLM: %s", exc)
            raise

    async def warmup(self) -> None:
        await self._llm.warmup()

    async def cerrar(self) -> None:
        cerrar = getattr(self._llm, "cerrar", None)
        if cerrar:
            await cerrar()

    # ===== Internos =================================================

    def _evaluar_estado(self) -> EstadoCircuito:
        """Transiciona el estado si corresponde y devuelve el estado actual."""
        ahora = time.monotonic()
        if self._estado == EstadoCircuito.ABIERTO:
            if ahora - self._ultimo_cambio >= self._reset:
                self._estado = EstadoCircuito.SEMIABIERTO
                log.info("circuit_breaker → SEMIABIERTO (probando)")
        elif self._estado == EstadoCircuito.CERRADO:
            recientes = [t for t in self._fallos if ahora - t < self._ventana]
            self._fallos = recientes
            if len(recientes) >= self._umbral:
                self._estado = EstadoCircuito.ABIERTO
                self._ultimo_cambio = ahora
                log.warning(
                    "circuit_breaker → ABIERTO (%d fallos en %ds)",
                    len(recientes), self._ventana,
                )
        return self._estado

    def _registrar_fallo(self) -> None:
        self._fallos.append(time.monotonic())
        if self._estado == EstadoCircuito.SEMIABIERTO:
            self._estado = EstadoCircuito.ABIERTO
            self._ultimo_cambio = time.monotonic()
            log.warning("circuit_breaker → ABIERTO (fallo en semiabierto)")

    def _registrar_exito(self) -> None:
        if self._estado == EstadoCircuito.SEMIABIERTO:
            self._estado = EstadoCircuito.CERRADO
            self._fallos.clear()
            log.info("circuit_breaker → CERRADO (recuperado)")
