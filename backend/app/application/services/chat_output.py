from __future__ import annotations

from dataclasses import dataclass, field
from uuid import UUID


@dataclass
class ChatOutput:
    """DTO de salida del caso de uso ProcesarChat."""

    sesion_id: UUID
    respuesta: str
    productos_citados: list[dict] = field(default_factory=list)
    productos_sugeridos: list[dict] = field(default_factory=list)
    pasos: list[dict] = field(default_factory=list)
