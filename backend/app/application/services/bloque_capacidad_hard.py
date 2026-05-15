from __future__ import annotations

import re

from ...domain.shared.normalizacion import NormalizadorTexto


class BloqueCapacidadHard:
    """SRP: detecta requisitos de capacidad mínima declarados por el cliente
    (kg para lavadoras, litros para refrigeradoras) e inyecta una directiva
    dura al LLM para que NO presente como recomendación principal ningún
    producto que no cumpla el mínimo y que avise explícitamente si no hay
    stock que lo cumpla."""

    _RX_KG_MIN = re.compile(
        r'\bminimo\s+(\d+)\s*(?:kg|kgs|kilos?)\b'
        r'|\b(\d+)\s*(?:kilos?|kg)\s+(?:minimo|minimos?|como\s+minimo)\b'
        r'|\bal\s+menos\s+(\d+)\s*(?:kg|kgs|kilos?)\b',
        re.IGNORECASE,
    )
    _RX_LITROS_MIN = re.compile(
        r'\bminimo\s+(\d+)\s*(?:litros?|lts?)\b'
        r'|\b(\d+)\s*(?:litros?|lts?)\s+(?:minimo|minimos?|como\s+minimo)\b'
        r'|\bal\s+menos\s+(\d+)\s*(?:litros?)\b',
        re.IGNORECASE,
    )
    _KW_LAVADORA = re.compile(r'\b(?:lavadora|lavasecadora)\b', re.IGNORECASE)
    _KW_REFRI = re.compile(
        r'\b(?:refrigeradora?|refri|heladera|refrigerador)\b', re.IGNORECASE
    )

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        if not mensaje:
            return None
        norm = NormalizadorTexto.normalizar(mensaje)
        partes: list[str] = []

        if cls._KW_LAVADORA.search(norm):
            kg = cls._extraer_valor(cls._RX_KG_MIN, norm)
            if kg is not None and kg >= 6:
                partes.append(
                    f"REQUISITO DURO — CAPACIDAD LAVADORA:\n"
                    f"  El cliente necesita MÍNIMO {kg:.0f} kg.\n"
                    f"  - Al llamar buscar_productos, pasá `capacidad_kg_min={kg:.0f}`.\n"
                    f"  - NUNCA etiquetes como 'comprar', 'apuesta segura', 'recomendada' "
                    f"ni 'recomendación principal' a una lavadora con capacidad inferior a {kg:.0f} kg.\n"
                    f"  - Si encontrás modelos con menos de {kg:.0f} kg, mostrarlos SOLO como "
                    f"'No cumple el requisito de capacidad' con la capacidad real visible.\n"
                    f"  - Si NO hay ninguna lavadora de {kg:.0f} kg o más en catálogo, decí "
                    f"exactamente: 'No encontré lavadoras automáticas de {kg:.0f} kg o más "
                    f"dentro del presupuesto.' Luego ofrecé la más cercana aclarando que "
                    f"no cumple el mínimo."
                )

        if cls._KW_REFRI.search(norm):
            litros = cls._extraer_valor(cls._RX_LITROS_MIN, norm)
            if litros is not None and litros >= 100:
                partes.append(
                    f"REQUISITO DURO — CAPACIDAD REFRIGERADORA:\n"
                    f"  El cliente necesita MÍNIMO {litros:.0f} litros.\n"
                    f"  - Al llamar buscar_productos, pasá `capacidad_litros_min={litros:.0f}`.\n"
                    f"  - NUNCA recomiendes como principal un modelo inferior a {litros:.0f} litros.\n"
                    f"  - Si no hay en catálogo, decilo explícitamente."
                )

        return "\n\n".join(partes) if partes else None

    @classmethod
    def _extraer_valor(cls, rx: re.Pattern, texto: str) -> float | None:
        m = rx.search(texto)
        if not m:
            return None
        val = next((g for g in m.groups() if g is not None), None)
        return float(val) if val else None
