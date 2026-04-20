from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
from uuid import UUID


@dataclass(frozen=True)
class RegistrarAlternativaOfrecidaCommand:
    """Command: anotar en el perfil la categoria/subcategoria alternativa que
    el agente ya le ofrecio al cliente (ej. 'Automotriz/Vehiculos' cuando
    pidio 'auto Tesla'). Sirve para que turnos siguientes no nieguen la
    misma categoria."""

    sesion_id: UUID
    categoria: str
    subcategoria: Optional[str] = None

    def formato_guardar(self) -> str:
        if self.subcategoria:
            return f"{self.categoria}/{self.subcategoria}"
        return self.categoria
