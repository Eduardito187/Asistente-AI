from __future__ import annotations

from dataclasses import dataclass

from ...domain.aprendizaje import ReasonCode, Severidad
from .validators import (
    BudgetValidator,
    CategoryConsistencyValidator,
    HardRequirementsValidator,
    NoBackendLeakValidator,
    ResponseFormatValidator,
    TechnicalClaimsValidator,
)


@dataclass(frozen=True)
class AutoQualityScore:
    """Score 0-100 + reason_code dominante + violaciones criticas."""
    score: int
    reason_code: ReasonCode
    severidad: Severidad
    violaciones: list[str]
    criterios_aprobados: list[str]
    apto_para_fewshot: bool


class AutoQualityScorer:
    """SRP: combinar 6 validators en un score 0-100. Decide si una conversacion
    puede convertirse en few-shot/auto-curada (#1 del review).

    Regla: cualquier validator critico que falla bloquea inmediatamente la
    promocion. Un score >= 85 sin criticos => apto."""

    UMBRAL_APTO = 85

    @classmethod
    def evaluar(
        cls,
        respuesta: str,
        productos: list[dict],
        perfil_estado: dict,
    ) -> AutoQualityScore:
        violaciones: list[str] = []
        criterios: list[str] = []
        criticas: list[ReasonCode] = []
        score = 100

        format_r = ResponseFormatValidator.validar(respuesta, productos)
        if not format_r.paso:
            score -= 20
            violaciones.append(f"format: {format_r.detalle}")
        else:
            criterios.append("format ok")

        leak_r = NoBackendLeakValidator.validar(respuesta)
        if not leak_r.paso:
            score -= 60
            criticas.append(leak_r.reason_code)
            violaciones.append(f"leak: {leak_r.detalle}")
        else:
            criterios.append("sin leaks")

        cat_r = CategoryConsistencyValidator.validar(perfil_estado, productos)
        if not cat_r.paso:
            score -= 50
            criticas.append(cat_r.reason_code)
            violaciones.append(f"cat: {cat_r.detalle}")
        else:
            criterios.append("categoria coherente")

        hard_r = HardRequirementsValidator.validar(perfil_estado, productos)
        if not hard_r.paso:
            score -= 50
            criticas.append(hard_r.reason_code)
            violaciones.append(f"hard: {hard_r.detalle}")
        else:
            criterios.append("hard requirements ok")

        tech_r = TechnicalClaimsValidator.validar(respuesta, productos)
        if not tech_r.paso:
            score -= 60
            criticas.append(tech_r.reason_code)
            violaciones.append(f"tech: {tech_r.detalle}")
        else:
            criterios.append("claims tecnicos ok")

        budg_r = BudgetValidator.validar(perfil_estado, productos)
        if not budg_r.paso:
            score -= 15
            violaciones.append(f"budget: {budg_r.detalle}")
        else:
            criterios.append("presupuesto ok")

        score = max(0, min(100, score))
        reason_dominante = criticas[0] if criticas else ReasonCode.OK
        severidad = (
            Severidad.CRITICAL if criticas
            else (Severidad.MEDIUM if score < cls.UMBRAL_APTO else Severidad.LOW)
        )
        apto = score >= cls.UMBRAL_APTO and not criticas
        return AutoQualityScore(
            score=score,
            reason_code=reason_dominante,
            severidad=severidad,
            violaciones=violaciones,
            criterios_aprobados=criterios,
            apto_para_fewshot=apto,
        )
