from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PasoAgente:
    """Registro de una invocacion tool dentro del loop del agente."""

    tool: str
    args: dict
    result: dict
    fallback: bool = False
