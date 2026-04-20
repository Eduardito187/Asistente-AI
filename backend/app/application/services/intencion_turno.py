from __future__ import annotations

from enum import Enum


class IntencionTurno(str, Enum):
    """Intencion unificada del turno del cliente (punto 4 de la spec).

    Agrupa las 18 intenciones del flujo conversacional. Solo las que tienen
    responder deterministico disparan short-circuit; el resto cae al LLM."""

    GREETING = "greeting"
    PRODUCT_SEARCH = "product_search"
    BUDGET_REFINEMENT = "budget_refinement"
    PREFERENCE_REFINEMENT = "preference_refinement"
    RECOMMENDATION_REQUEST = "recommendation_request"
    COMPARISON_REQUEST = "comparison_request"
    ALTERNATIVE_CHEAPER = "alternative_cheaper"
    ALTERNATIVE_BETTER = "alternative_better"
    ALTERNATIVE_OTHER = "alternative_other"
    STOCK_CHECK = "stock_check"
    DELIVERY_QUERY = "delivery_query"
    PAYMENT_QUERY = "payment_query"
    FINANCING_QUERY = "financing_query"
    OBJECTION_PRICE = "objection_price"
    OBJECTION_TRUST = "objection_trust"
    QUOTE_REQUEST = "quote_request"
    PURCHASE_INTENT = "purchase_intent"
    ADD_TO_CART = "add_to_cart"
    POST_SALE = "post_sale"
    UNKNOWN = "unknown"
