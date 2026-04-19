from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from uuid import UUID


@dataclass
class ConversacionCurada:
    """Ejemplo "bueno" usado como few-shot dinamico. SRP: modelar el par
    cliente/asistente que queremos que el modelo imite en futuras conversaciones."""

    id: Optional[int]
    sesion_id: Optional[UUID]
    etiqueta: Optional[str]
    cliente_texto: str
    asistente_texto: str
    score: int
    turnos: int
    llevo_a_orden: bool
    activa: bool
    created_at: datetime
    updated_at: datetime
