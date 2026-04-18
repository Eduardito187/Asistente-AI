from __future__ import annotations

import json
from uuid import UUID

from ..ports.llm_port import LLMPort
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
        max_iter: int = 6,
    ) -> None:
        self._llm = llm
        self._dispatcher = dispatcher
        self._max_iter = max_iter

    async def conversar(self, sesion_id: UUID, historial: list[dict]) -> RespuestaAgente:
        mensajes: list[dict] = [{"role": "system", "content": SYSTEM_PROMPT}, *historial]
        trace: list[PasoAgente] = []
        skus: list[str] = []

        for _ in range(self._max_iter):
            msg = await self._llm.chat(mensajes, TOOLS_SPEC)
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
                resultado = self._dispatcher.ejecutar(nombre, args, sesion_id)

                trace.append(PasoAgente(tool=nombre, args=args, result=resultado))
                skus.extend(SkuExtractor.extraer(resultado))

                mensajes.append(
                    {"role": "tool", "content": json.dumps(resultado, ensure_ascii=False, default=str)}
                )

        return RespuestaAgente(
            texto="Disculpa, se me complico resolver tu consulta. Contame de otra forma que necesitas.",
            trace=trace,
            skus_tocados=SkuExtractor.dedupe(skus),
        )
