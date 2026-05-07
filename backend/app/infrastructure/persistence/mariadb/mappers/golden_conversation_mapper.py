from __future__ import annotations

import json

from .....domain.golden_conversations import GoldenConversation


class GoldenConversationMapper:
    @staticmethod
    def from_row(r: dict) -> GoldenConversation:
        errores = r.get("errores_que_previene")
        if isinstance(errores, str):
            try:
                errores = json.loads(errores)
            except (TypeError, ValueError):
                errores = []
        return GoldenConversation(
            id=r["id"],
            caso_que_cubre=r["caso_que_cubre"],
            categoria=r.get("categoria"),
            intencion=r.get("intencion"),
            uso=r.get("uso"),
            cliente_texto=r["cliente_texto"],
            asistente_texto=r["asistente_texto"],
            prioridad=int(r.get("prioridad") or 100),
            activo=bool(r.get("activo")),
            errores_que_previene=errores or [],
            created_at=r.get("created_at"),
            updated_at=r.get("updated_at"),
        )
