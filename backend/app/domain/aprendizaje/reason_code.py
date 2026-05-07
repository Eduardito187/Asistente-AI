from __future__ import annotations

from enum import Enum


class ReasonCode(str, Enum):
    """Codigos estandar de fallo y aprendizaje. Sirven para clasificar y
    medir tendencias en lugar de free-text. Mapean 1:1 a los puntos del
    review del usuario (#11)."""

    CONTEXT_LOST = "CONTEXT_LOST"
    CATEGORY_MISMATCH = "CATEGORY_MISMATCH"
    ATTRIBUTE_NOT_PARSED = "ATTRIBUTE_NOT_PARSED"
    HARD_FILTER_IGNORED = "HARD_FILTER_IGNORED"
    TECHNICAL_DATA_MISSING = "TECHNICAL_DATA_MISSING"
    TECHNICAL_HALLUCINATION = "TECHNICAL_HALLUCINATION"
    WRONG_FALLBACK = "WRONG_FALLBACK"
    BACKEND_ERROR_VISIBLE = "BACKEND_ERROR_VISIBLE"
    BAD_RANKING = "BAD_RANKING"
    BAD_FORMAT = "BAD_FORMAT"
    TOO_MANY_OPTIONS = "TOO_MANY_OPTIONS"
    LOW_END_FOR_PREMIUM = "LOW_END_FOR_PREMIUM"
    INTENT_DETECTION_FAILED = "INTENT_DETECTION_FAILED"
    NO_RESULTS = "NO_RESULTS"
    CATALOG_DATA_MISSING = "CATALOG_DATA_MISSING"
    UNSAFE_COMMERCIAL_CLAIM = "UNSAFE_COMMERCIAL_CLAIM"
    MAX_ITER_NO_TEXT = "MAX_ITER_NO_TEXT"
    QUALITY_GATE_FAILED = "QUALITY_GATE_FAILED"
    # Subtipos especificos del feedback 2026-05-07 (mas accionables que
    # los codigos genericos para correlacionar fallos con casos concretos).
    CATEGORY_MISMATCH_PORTATIL = "CATEGORY_MISMATCH_PORTATIL"
    CATEGORY_MISMATCH_RANDOM_PRODUCTS = "CATEGORY_MISMATCH_RANDOM_PRODUCTS"
    HARD_FILTER_RAM_STORAGE_IGNORED = "HARD_FILTER_RAM_STORAGE_IGNORED"
    FREE_TEXT_COMPARISON_FAILED = "FREE_TEXT_COMPARISON_FAILED"
    WRONG_HANDOFF = "WRONG_HANDOFF"
    OK = "OK"

    @classmethod
    def es_critico(cls, code: "ReasonCode | str") -> bool:
        c = code if isinstance(code, ReasonCode) else ReasonCode(code)
        return c in {
            cls.CATEGORY_MISMATCH,
            cls.CATEGORY_MISMATCH_PORTATIL,
            cls.CATEGORY_MISMATCH_RANDOM_PRODUCTS,
            cls.HARD_FILTER_IGNORED,
            cls.HARD_FILTER_RAM_STORAGE_IGNORED,
            cls.TECHNICAL_HALLUCINATION,
            cls.BACKEND_ERROR_VISIBLE,
            cls.UNSAFE_COMMERCIAL_CLAIM,
            cls.FREE_TEXT_COMPARISON_FAILED,
            cls.WRONG_HANDOFF,
        }
