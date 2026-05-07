from __future__ import annotations

import re


class DetectorUrgencia:
    """Detecta urgencia temporal del cliente para priorizar productos con
    stock disponible y entrega rápida.

    Frases típicas:
    - "lo necesito hoy" / "para mañana" / "urgente" / "ya"
    - "lo más rápido posible" / "cuanto antes" / "es para una emergencia"
    - "hoy mismo" / "esta tarde" / "esta semana"

    No corta el flujo — alimenta bloque de contexto al LLM para que filtre
    por solo_con_stock=True, prefiera envio_rapido=True, y mencione tiempos
    de entrega."""

    _RX = re.compile(
        r"(?:"
        # Urgencia explícita
        r"\burgent\w*\b"
        r"|\bes\s+urgente\b"
        r"|\bcorre\s+prisa\b"
        r"|\bcuanto\s+antes\b"
        r"|\bya\s+(?:mismo|mismito)\b"
        r"|\b(?:r[áa]pido|r[áa]pidamente)\s+(?:posible|por\s+favor)"
        r"|\blo\s+m[áa]s\s+r[áa]pido\s+posible\b"
        r"|\binmediato\b|\binmediatamente\b"
        # Tiempo limitado / hoy / mañana
        r"|\bpara\s+(?:hoy|mañana|esta\s+(?:tarde|noche|semana))"
        r"|\bhoy\s+mismo\b"
        r"|\blo\s+necesito\s+(?:hoy|mañana|ya|ahora|para)"
        r"|\bnecesito\s+(?:que\s+(?:llegue|me\s+lleg[ou]e)\s+(?:hoy|mañana|esta))"
        r"|\b(?:hasta|antes\s+de|antes\s+del?)\s+(?:hoy|mañana|el\s+\w+|las?\s+\d)"
        r"|\b(?:tengo|hay)\s+que\s+tener[lo]\w*\s+(?:hoy|mañana|para\s+\w+)"
        # Emergencia / regalo de último momento
        r"|\bemergencia\b"
        r"|\bes\s+para\s+(?:una\s+)?(?:emergencia|sorpresa|cumple\s+(?:de\s+)?hoy|"
        r"regalo\s+de\s+(?:hoy|mañana))"
        r"|\bme\s+olvid[ée](?:e|aba)\s+y"
        r"|\bsobre\s+la\s+hora\b"
        r"|\b[úu]ltimo\s+momento\b"
        # Eventos próximos como contexto temporal
        r"|\bes\s+para\s+(?:el\s+)?(?:viaje|cumple|boda|evento)\s+(?:de\s+)?(?:hoy|mañana|el\s+\w+)"
        r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_urgente(cls, mensaje: str) -> bool:
        if not mensaje:
            return False
        return bool(cls._RX.search(mensaje))
