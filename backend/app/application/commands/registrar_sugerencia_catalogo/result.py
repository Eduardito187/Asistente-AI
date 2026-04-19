from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RegistrarSugerenciaCatalogoResult:
    """Resultado: id de la sugerencia y si era nueva o fue un incremento."""

    sugerencia_id: int
    creada: bool
    veces_solicitado: int
