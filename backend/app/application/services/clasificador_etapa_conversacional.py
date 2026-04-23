from __future__ import annotations

import re
from enum import Enum
from typing import Optional


class EtapaConversacional(str, Enum):
    """Etapas de compra por las que pasa una conversación. El dispatcher las
    usa para decidir si permitir acciones transaccionales (agregar_al_carrito,
    confirmar_orden) o restringir al modo asesor."""

    EXPLORACION = "exploracion"     # cliente recién llega, orientación general
    REFINAMIENTO = "refinamiento"   # ya hay categoría/foco, ajustando filtros
    COMPARACION = "comparacion"     # pidió comparar o evaluar entre modelos
    DECISION = "decision"           # señales claras de intención de compra
    COMPRA = "compra"               # decidió, mandando al carrito/checkout


class ClasificadorEtapaConversacional:
    """SRP: deduce la etapa conversacional a partir del estado de la sesión
    (perfil) y las señales del turno actual. NO persiste — es derivado.

    Orden de precedencia (mayor gana):
      COMPRA > DECISION > COMPARACION > REFINAMIENTO > EXPLORACION
    """

    _RX_INTENCION_COMPRA = re.compile(
        r"\b(?:"
        r"lo\s+llevo|me\s+lo\s+llevo|"
        r"agrega(?:lo|r|melo)?(?:\s+al\s+carrito)?|"
        r"(?:quiero|deseo|voy\s+a)\s+comprarlo|"
        r"confirma(?:r|melo)?|"
        r"cerremos|cierra\s+(?:la\s+)?compra|"
        r"cuanto\s+es\s+en\s+total"
        r")\b",
        re.IGNORECASE,
    )

    _RX_DECISION = re.compile(
        r"\b(?:"
        r"me\s+decido\s+por|"
        r"elijo\s+(?:el|la|los|las)|"
        r"prefiero\s+(?:el|la)|"
        r"(?:quiero|elegi[ríé])\s+(?:el|la|ese|esa)|"
        r"vamos\s+con\s+(?:el|la|ese|esa)"
        r")\b",
        re.IGNORECASE,
    )

    @classmethod
    def clasificar(
        cls,
        mensaje: str | None,
        perfil,
        trace: list,
        carrito_no_vacio: bool = False,
    ) -> EtapaConversacional:
        # Compra: ya hay acción transaccional exitosa o frase de cierre
        if cls._tiene_accion_carrito_exitosa(trace) or cls._es_intencion_compra(mensaje):
            return EtapaConversacional.COMPRA
        # Decisión: frase clara de "elijo / prefiero / vamos con el X"
        if cls._es_decision(mensaje) or carrito_no_vacio:
            return EtapaConversacional.DECISION
        # Comparación: llamó comparar_productos en este turno o el anterior
        if cls._hubo_comparacion(trace):
            return EtapaConversacional.COMPARACION
        # Refinamiento: ya hay foco/categoría en perfil
        if cls._tiene_foco(perfil):
            return EtapaConversacional.REFINAMIENTO
        return EtapaConversacional.EXPLORACION

    @classmethod
    def permite_transaccion(cls, etapa: EtapaConversacional, mensaje: str | None) -> bool:
        """Gate: si la etapa permite ejecutar agregar_al_carrito o
        confirmar_orden. Solo decisión/compra sin señal explícita no basta —
        requerimos la frase explícita del cliente."""
        if etapa == EtapaConversacional.COMPRA:
            return True
        if etapa == EtapaConversacional.DECISION:
            return cls._es_intencion_compra(mensaje) or cls._es_decision(mensaje)
        return False

    # ----------- helpers de clasificación -----------
    @classmethod
    def _es_intencion_compra(cls, mensaje: str | None) -> bool:
        return bool(mensaje and cls._RX_INTENCION_COMPRA.search(mensaje))

    @classmethod
    def _es_decision(cls, mensaje: str | None) -> bool:
        return bool(mensaje and cls._RX_DECISION.search(mensaje))

    @staticmethod
    def _tiene_accion_carrito_exitosa(trace: list) -> bool:
        return any(
            getattr(p, "tool", None) in ("agregar_al_carrito", "confirmar_orden")
            and not (getattr(p, "result", {}) or {}).get("error")
            for p in (trace or [])
        )

    @staticmethod
    def _hubo_comparacion(trace: list) -> bool:
        return any(
            getattr(p, "tool", None) == "comparar_productos"
            and not (getattr(p, "result", {}) or {}).get("error")
            for p in (trace or [])
        )

    @staticmethod
    def _tiene_foco(perfil) -> bool:
        return bool(
            getattr(perfil, "sku_foco", None)
            or getattr(perfil, "categoria_foco", None)
            or getattr(perfil, "subcategoria_foco", None)
        )
