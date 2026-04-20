from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RespuestaFollowUp:
    """DTO emitido por un responder deterministico cuando intercepta el turno.

    Cuando un responder devuelve esta estructura, ProcesarChatService salta
    al LLM: el texto ya esta armado y los productos/skus van directo a la
    UI, analogo a la respuesta del atajo por SKU directo. `ruta` identifica
    la sub-ruta para metricas (ej 'follow_up_mas_barato')."""

    texto: str
    productos: list[dict] = field(default_factory=list)
    skus: list[str] = field(default_factory=list)
    ruta: str = "follow_up"
