from __future__ import annotations

from enum import Enum


class SynonymType(str, Enum):
    """Tipologia de candidato de sinonimo (#3 del review).

    No todos van a la misma tabla: typo->correccion automatica;
    use_case->use_case_keywords no a categorias_sinonimos."""

    TYPO = "typo"
    CATEGORY_ALIAS = "category_alias"
    PRODUCT_ALIAS = "product_alias"
    BRAND_ALIAS = "brand_alias"
    TECHNICAL_ATTRIBUTE = "technical_attribute"
    USE_CASE = "use_case"
    LOCAL_EXPRESSION = "local_expression"
    UNKNOWN = "unknown"
