from __future__ import annotations

import json
from uuid import UUID

from ..commands.registrar_conversacion_fallida import (
    RegistrarConversacionFallidaCommand,
    RegistrarConversacionFallidaHandler,
)
from ..ports.llm_port import LLMPort
from ..services.detector_loop_tool import DetectorLoopTool
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
        registrar_fallida: RegistrarConversacionFallidaHandler | None = None,
    ) -> None:
        self._llm = llm
        self._dispatcher = dispatcher
        self._inyector = inyector_fewshot
        self._max_iter = max_iter
        self._registrar_fallida = registrar_fallida

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
                self._procesar_tool_call(
                    tc, sesion_id, marca_indiferente, mensaje_usuario,
                    trace, skus, mensajes,
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
        self._registrar_fallo(sesion_id, mensaje_usuario, trace, "max_iter_sin_texto")
        return RespuestaAgente(
            texto=texto_fallback,
            trace=trace,
            skus_tocados=SkuExtractor.dedupe(skus),
        )

    def _procesar_tool_call(
        self,
        tc: dict,
        sesion_id: UUID,
        marca_indiferente: bool,
        mensaje_usuario: str,
        trace: list,
        skus: list,
        mensajes: list,
    ) -> None:
        """Ejecuta una tool call individual, actualiza trace/skus, e inyecta
        mensaje correctivo al LLM si DetectorLoopTool detecta patrón nocivo."""
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

        # Anti-loop: si el LLM se estanca en un patrón nocivo
        # (ver_producto con SKUs inventados, buscar_productos con
        # resultados vacíos), inyectamos un mensaje correctivo en el
        # resultado para forzar cambio de estrategia.
        correctivo = DetectorLoopTool.correctivo(trace, nombre, resultado)
        resultado_para_llm = (
            {**resultado, "_instruccion_sistema": correctivo}
            if correctivo else resultado
        )
        mensajes.append({
            "role": "tool",
            "content": json.dumps(resultado_para_llm, ensure_ascii=False, default=str),
        })

    def _registrar_fallo(
        self, sesion_id: UUID, mensaje_usuario: str, trace: list, razon: str
    ) -> None:
        """Persiste turno fallido para failure-mining. Falla silenciosa."""
        if self._registrar_fallida is None:
            return
        ultimo_args = next(
            (p.args for p in reversed(trace) if p.tool == "buscar_productos"), None
        )
        trace_resumen = " | ".join(f"{p.tool}({list(p.args.keys())[:3]})" for p in trace[-5:])
        try:
            self._registrar_fallida.ejecutar(RegistrarConversacionFallidaCommand(
                sesion_id=sesion_id,
                mensaje_usuario=mensaje_usuario,
                perfil_estado={"tools_invocadas": [p.tool for p in trace]},
                ultimo_buscar_args=ultimo_args,
                razon_fallo=razon,
                trace_resumen=trace_resumen,
            ))
        except Exception:
            pass
