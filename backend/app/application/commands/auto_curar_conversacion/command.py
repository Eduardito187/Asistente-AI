from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class AutoCurarConversacionCommand:
    """Persiste un turno como ConversacionCurada SOLO si pasa quality gate.
    Antes promovia por sola heuristica de turno exitoso; ahora requiere
    AutoQualityScorer.apto_para_fewshot=True (#1, #4 del review)."""

    sesion_id: Optional[UUID]
    cliente_texto: str
    asistente_texto: str
    score: int
    etiqueta: Optional[str] = None
    productos_citados: list[dict] = field(default_factory=list)
    perfil_estado: dict = field(default_factory=dict)
    prompt_version: Optional[str] = None
