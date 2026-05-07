from __future__ import annotations

import re


class DetectorRequisitosNDObligatorios:
    """SRP: detecta cuando el cliente menciona specs cuya ausencia en ficha
    es probable y por lo tanto exigen el aviso 'No tengo ese dato en la
    ficha tecnica' por cada producto citado.

    Cubre los casos del feedback 2026-05-07:
    - TV gaming/PS5 -> HDMI 2.1 + 120Hz
    - Refri eficiente -> inverter
    - Laptop pro -> GPU dedicada
    - Audifonos -> ANC
    - Generales -> garantia oficial extendida"""

    _PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("HDMI 2.1", re.compile(
            r"\bhdmi\s*2\.1\b|\bps5\b|\bxbox\s*series\s*x\b|\bnext\s*gen\b",
            re.IGNORECASE,
        )),
        ("120Hz / refresh rate", re.compile(
            r"\b1[24]4\s*hz\b|\b120\s*hz\b|\bps5\b|\brefresh\s*rate\b|\bvrr\b|\ballm\b|\bgaming\b",
            re.IGNORECASE,
        )),
        ("Inverter (motor)", re.compile(
            r"\binverter\b", re.IGNORECASE,
        )),
        ("GPU dedicada (RTX/GTX/Radeon)", re.compile(
            r"\bgpu\s+(?:dedicada|discreta)\b|\bgr[áa]fica\s+dedicada\b"
            r"|\btarjeta\s+gr[áa]fica\b|\brtx\b|\bgtx\b|\bgeforce\b|\bradeon\b",
            re.IGNORECASE,
        )),
        ("ANC (cancelacion activa)", re.compile(
            r"\banc\b|\bcancelaci[oó]n\s+(?:activa|de\s+ruido)\b|\bnoise\s+cancel",
            re.IGNORECASE,
        )),
        ("Garantia oficial extendida", re.compile(
            r"\bgarant[ií]a\s+(?:oficial|extendida|larga)\b",
            re.IGNORECASE,
        )),
        ("Estabilizacion optica de imagen (OIS)", re.compile(
            r"\bois\b|\bestabilizaci[oó]n\s+(?:[oó]ptica|de\s+imagen)\b",
            re.IGNORECASE,
        )),
        ("Camara nocturna avanzada", re.compile(
            r"\bmodo\s+nocturno\b|\bnight\s+mode\b|\bfoto\s+nocturna\b|\bnight\s+sight\b",
            re.IGNORECASE,
        )),
    )

    @classmethod
    def requisitos(cls, mensaje: str) -> list[str]:
        if not mensaje:
            return []
        return [etiqueta for etiqueta, rx in cls._PATRONES if rx.search(mensaje)]
