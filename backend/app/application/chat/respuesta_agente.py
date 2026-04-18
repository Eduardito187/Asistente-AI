from __future__ import annotations

from dataclasses import dataclass, field

from .paso_agente import PasoAgente


@dataclass
class RespuestaAgente:
    """Resultado final del loop del agente tras agotar tool-calling."""

    texto: str
    trace: list[PasoAgente] = field(default_factory=list)
    skus_tocados: list[str] = field(default_factory=list)
