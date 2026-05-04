from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class PrioridadSlot:
    nivel: int
    texto: str
    es_dura: bool  # True = filtro obligatorio, False = preferencia blanda


class DetectorPrioridadesJerarquicas:
    """Parsea sintaxis 'Prioridad N: texto' en mensajes de usuario."""

    _RX = re.compile(r"prioridad\s*([1-9])\s*:\s*([^\n.;]+)", re.IGNORECASE)
    _SOFT_TOKENS = frozenset({
        "preferible", "prefiero", "si es posible", "si hay", "si existe",
        "si tienen", "si puedes", "de ser posible", "ojalá", "ojala",
        "me gustaría", "me gustaria", "idealmente", "si se puede",
    })

    @classmethod
    def detectar(cls, mensaje: str) -> list[PrioridadSlot]:
        resultado = []
        for m in cls._RX.finditer(mensaje or ""):
            nivel = int(m.group(1))
            texto = m.group(2).strip()
            es_dura = not any(t in texto.lower() for t in cls._SOFT_TOKENS)
            resultado.append(PrioridadSlot(nivel=nivel, texto=texto, es_dura=es_dura))
        return sorted(resultado, key=lambda s: s.nivel)

    @classmethod
    def hay_prioridades(cls, mensaje: str) -> bool:
        return bool(cls._RX.search(mensaje or ""))

    @classmethod
    def formatear(cls, slots: list[PrioridadSlot]) -> str:
        if not slots:
            return ""
        lineas = ["PRIORIDADES DECLARADAS POR EL CLIENTE (respetar en orden estricto):"]
        for s in slots:
            if s.es_dura:
                tipo = "OBLIGATORIO — si no cumple, NO mostrar como recomendación principal"
            else:
                tipo = "PREFERIBLE — ranking hint, no es filtro duro"
            lineas.append(f"  P{s.nivel} [{tipo}]: {s.texto}")
        lineas += [
            "Reglas:",
            "  · Si P1 no se cumple → producto solo como alternativa secundaria, nunca como principal.",
            "  · Si falta dato para verificar P1 → di exactamente: "
            "'No puedo confirmar [P1] — no tengo ese dato en ficha'.",
            "  · Prioridades más bajas que la primera fallida no salvan al producto.",
        ]
        return "\n".join(lineas)
