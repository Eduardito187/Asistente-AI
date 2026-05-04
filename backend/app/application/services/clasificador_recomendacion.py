from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class NivelRecomendacion(str, Enum):
    IDEAL = "ideal"                # cumple todo + datos completos
    RECOMENDABLE = "recomendable"  # cumple lo critico
    COMPATIBLE = "compatible"      # cumple parcial, con limitaciones
    NO_RECOMENDABLE = "no_recomendable"  # no cumple obligatorios


@dataclass(frozen=True)
class Clasificacion:
    nivel: NivelRecomendacion
    motivo: str
    puede_ser_principal: bool


class ClasificadorRecomendacion:
    """SRP: clasificar cada producto como Principal/Alternativa/No-recomendable
    a partir del scoring. Sin esta capa, el LLM mete entradas debiles como
    'opciones'."""

    @classmethod
    def clasificar(cls, producto, perfil) -> Clasificacion:
        from .scoring_comercial import ScoringComercial
        puntaje = ScoringComercial.calcular(producto, perfil)
        if puntaje.falta:
            return Clasificacion(
                nivel=NivelRecomendacion.NO_RECOMENDABLE,
                motivo=f"no cumple: {', '.join(puntaje.falta)}",
                puede_ser_principal=False,
            )
        if puntaje.score >= 80 and not puntaje.advertencias:
            return Clasificacion(
                nivel=NivelRecomendacion.IDEAL,
                motivo="cumple todo con datos completos",
                puede_ser_principal=True,
            )
        if puntaje.score >= 60:
            motivo = "cumple lo critico"
            if puntaje.advertencias:
                motivo += f" (advertencia: {puntaje.advertencias[0]})"
            return Clasificacion(
                nivel=NivelRecomendacion.RECOMENDABLE,
                motivo=motivo,
                puede_ser_principal=True,
            )
        if puntaje.score >= 30:
            return Clasificacion(
                nivel=NivelRecomendacion.COMPATIBLE,
                motivo="cumple parcial — alternativa con limitaciones",
                puede_ser_principal=False,
            )
        return Clasificacion(
            nivel=NivelRecomendacion.NO_RECOMENDABLE,
            motivo=f"score bajo ({puntaje.score})",
            puede_ser_principal=False,
        )
