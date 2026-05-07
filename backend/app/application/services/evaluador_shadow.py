from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from sqlalchemy import text

from ..ports import UnitOfWork
from .auto_quality_scorer import AutoQualityScorer


@dataclass(frozen=True)
class ResultadoEvaluacion:
    origen: str
    origen_id: int
    reason_code_anterior: str | None
    reason_code_nuevo: str
    score_nuevo: int
    veredicto: str  # "fixed" | "still_broken" | "regression" | "unchanged"
    detalle: str


class EvaluadorShadow:
    """SRP: re-evaluar materiales historicos contra los validators ACTUALES.

    Dos casos de uso (#17 review):

    1. Re-correr validators sobre `conversaciones_fallidas` antiguas:
       si hoy el quality gate detectaria el mismo fallo o si la nueva
       version lo hubiera evitado (insumo para mejoras de prompt/codigo).

    2. Re-correr validators sobre `conversaciones_curadas` activas:
       deteccion de drift — si una curada vieja ahora falla validators
       nuevos, marcarla para revision manual.

    No invoca al LLM. Solo aplica los validators al material persistido."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def evaluar_fallos_recientes(self, limite: int = 50) -> list[ResultadoEvaluacion]:
        with self._uow_factory() as uow:
            fallidas = uow.conversaciones_fallidas.listar_recientes(limite=limite)
        resultados: list[ResultadoEvaluacion] = []
        for f in fallidas:
            score = AutoQualityScorer.evaluar(
                respuesta=f.mensaje_usuario or "",
                productos=[],
                perfil_estado=f.perfil_estado or {},
            )
            resultados.append(ResultadoEvaluacion(
                origen="conversaciones_fallidas",
                origen_id=f.id or 0,
                reason_code_anterior=self._extraer_reason(f.razon_fallo or ""),
                reason_code_nuevo=score.reason_code.value,
                score_nuevo=score.score,
                veredicto=self._veredicto_fallos(score),
                detalle=", ".join(score.violaciones[:3]) or "ok",
            ))
        self._persistir(resultados)
        return resultados

    def evaluar_curadas_activas(self, limite: int = 50) -> list[ResultadoEvaluacion]:
        """Drift check: ¿alguna curada activa hoy reprueba el quality gate?"""
        with self._uow_factory() as uow:
            curadas = uow.conversaciones_curadas.top_activas(limite=limite)
        resultados: list[ResultadoEvaluacion] = []
        for c in curadas:
            score = AutoQualityScorer.evaluar(
                respuesta=c.asistente_texto or "",
                productos=[],
                perfil_estado={},
            )
            veredicto = "drift" if not score.apto_para_fewshot else "ok"
            resultados.append(ResultadoEvaluacion(
                origen="conversaciones_curadas",
                origen_id=c.id or 0,
                reason_code_anterior=None,
                reason_code_nuevo=score.reason_code.value,
                score_nuevo=score.score,
                veredicto=veredicto,
                detalle=", ".join(score.violaciones[:3]) or "ok",
            ))
        self._persistir(resultados)
        return resultados

    @staticmethod
    def _extraer_reason(razon_texto: str) -> str | None:
        """Extrae el reason_code embedded si existe en el texto del fallo."""
        upper = razon_texto.upper()
        for token in (
            "CATEGORY_MISMATCH", "HARD_FILTER_IGNORED", "TECHNICAL_HALLUCINATION",
            "BACKEND_ERROR_VISIBLE", "MAX_ITER_NO_TEXT", "NO_RESULTS",
        ):
            if token in upper:
                return token
        return None

    @staticmethod
    def _veredicto_fallos(score) -> str:
        if score.apto_para_fewshot:
            return "fixed"
        if score.reason_code.value == "OK":
            return "unchanged"
        return "still_broken"

    def _persistir(self, resultados: list[ResultadoEvaluacion]) -> None:
        if not resultados:
            return
        from ...application.chat.system_prompt import PROMPT_VERSION
        try:
            with self._uow_factory() as uow:
                sess = uow._session
                for r in resultados:
                    sess.execute(
                        text(
                            "INSERT INTO evaluaciones_shadow "
                            "(origen, origen_id, prompt_version_evaluado, "
                            " reason_code_anterior, reason_code_nuevo, score_nuevo, "
                            " veredicto, detalle) "
                            "VALUES (:o, :oid, :pv, :ra, :rn, :sn, :v, :d)"
                        ),
                        {
                            "o": r.origen, "oid": r.origen_id,
                            "pv": PROMPT_VERSION,
                            "ra": r.reason_code_anterior, "rn": r.reason_code_nuevo,
                            "sn": r.score_nuevo, "v": r.veredicto,
                            "d": r.detalle[:500],
                        },
                    )
                uow.commit()
        except Exception:
            pass
