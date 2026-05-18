from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FilaCoberturaAtributos:
    categoria: str
    total: int
    atributos: dict[str, int]     # campo → cantidad con valor no-NULL
    porcentajes: dict[str, float]  # campo → % de cobertura


@dataclass
class ResultadoCoberturaAtributos:
    global_: FilaCoberturaAtributos
    por_categoria: list[FilaCoberturaAtributos] = field(default_factory=list)
