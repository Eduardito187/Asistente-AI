from __future__ import annotations

import json
from uuid import UUID

from .....domain.conversaciones_fallidas import ConversacionFallida


class ConversacionFallidaMapper:
    """Materializa un ConversacionFallida desde un row crudo."""

    @staticmethod
    def from_row(r: dict) -> ConversacionFallida:
        sid = r.get("sesion_id")
        return ConversacionFallida(
            id=r["id"],
            sesion_id=UUID(sid) if sid else None,
            mensaje_usuario=r.get("mensaje_usuario") or "",
            perfil_estado=ConversacionFallidaMapper._loads(r.get("perfil_estado")),
            ultimo_buscar_args=ConversacionFallidaMapper._loads(r.get("ultimo_buscar_args")),
            razon_fallo=r.get("razon_fallo") or "",
            trace_resumen=r.get("trace_resumen"),
            creado_en=r["creado_en"],
        )

    @staticmethod
    def _loads(raw):
        if not raw:
            return {}
        if isinstance(raw, dict):
            return raw
        try:
            return json.loads(raw)
        except (TypeError, ValueError):
            return {}
