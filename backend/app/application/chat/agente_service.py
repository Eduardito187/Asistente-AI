from __future__ import annotations

import json
from uuid import UUID

from ..ports.llm_port import LLMPort
from ..services.inyector_fewshot import InyectorFewShot
from ..services.sintetizador_respuesta_trace import SintetizadorRespuestaTrace
from .helpers import SkuExtractor, ValueParser
from .paso_agente import PasoAgente
from .respuesta_agente import RespuestaAgente
from .system_prompt import SYSTEM_PROMPT
from .tool_definitions import TOOLS_SPEC
from .tool_dispatcher import ToolDispatcher


class AgenteService:
    """Orquesta el loop tool-calling. Unica responsabilidad: el loop."""

    def __init__(
        self,
        llm: LLMPort,
        dispatcher: ToolDispatcher,
        inyector_fewshot: InyectorFewShot,
        max_iter: int = 3,
    ) -> None:
        self._llm = llm
        self._dispatcher = dispatcher
        self._inyector = inyector_fewshot
        self._max_iter = max_iter

    async def conversar(
        self,
        sesion_id: UUID,
        historial: list[dict],
        contexto_turno: str | None = None,
        marca_indiferente: bool = False,
    ) -> RespuestaAgente:
        bloque_fewshot = self._inyector.bloque()
        partes = [SYSTEM_PROMPT]
        if bloque_fewshot:
            partes.append(bloque_fewshot)
        if contexto_turno:
            partes.append(contexto_turno)
        system_content = "\n\n".join(partes)
        mensajes: list[dict] = [{"role": "system", "content": system_content}, *historial]
        trace: list[PasoAgente] = []
        skus: list[str] = []
        # último mensaje del cliente — necesario para que el dispatcher aplique
        # gates conversacionales (ej. no agregar al carrito sin señal de compra).
        mensaje_usuario = next(
            (m["content"] for m in reversed(historial) if m.get("role") == "user"),
            "",
        )

        for i in range(self._max_iter):
            ultima_iter = i == self._max_iter - 1
            tools = [] if ultima_iter else TOOLS_SPEC
            msg = await self._llm.chat(mensajes, tools)
            mensajes.append(msg.to_dict())

            if not msg.tool_calls:
                return RespuestaAgente(
                    texto=(msg.content or "").strip(),
                    trace=trace,
                    skus_tocados=SkuExtractor.dedupe(skus),
                )

            for tc in msg.tool_calls:
                fn = tc.get("function") or {}
                nombre = fn.get("name", "")
                args = ValueParser.parse_args(fn.get("arguments"))
                resultado = self._dispatcher.ejecutar(
                    nombre, args, sesion_id,
                    marca_indiferente=marca_indiferente,
                    mensaje_usuario=mensaje_usuario,
                    trace_actual=trace,
                )

                trace.append(PasoAgente(tool=nombre, args=args, result=resultado))
                skus.extend(SkuExtractor.extraer(resultado))

                mensajes.append(
                    {"role": "tool", "content": json.dumps(resultado, ensure_ascii=False, default=str)}
                )

        # Si el LLM consumio todas las iteraciones sin responder, hacemos una
        # llamada final SIN tools para forzar texto. Si igual no devuelve nada,
        # sintetizamos desde el trace (productos encontrados) en vez del canned.
        msg_final = await self._llm.chat(mensajes, [])
        texto = (msg_final.content or "").strip()
        if texto:
            return RespuestaAgente(texto=texto, trace=trace, skus_tocados=SkuExtractor.dedupe(skus))
        texto_fallback = SintetizadorRespuestaTrace.sintetizar(trace) or (
            "Encontré opciones en el catálogo. Contame qué te importa más "
            "(presupuesto, marca o uso) para ajustar la recomendación."
        )
        return RespuestaAgente(
            texto=texto_fallback,
            trace=trace,
            skus_tocados=SkuExtractor.dedupe(skus),
        )
