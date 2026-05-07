from __future__ import annotations

import re


class BloqueFallbackMarca:
    """SRP: cuando el cliente declaro una marca preferida pero acepta
    fallbacks (ej. 'preferia Samsung, pero acepto iPhone o Xiaomi'),
    inyecta directiva para que la respuesta:

    1. Avise explicitamente que NO hay stock de la marca preferida.
    2. Justifique POR QUE la alternativa elegida cumple/no cumple el resto
       de criterios (ej. 'iPhone 14 tiene 128GB, no 256GB que pediste —
       si priorizas almacenamiento, elegiria otra opcion').
    3. Compare con al menos 2 alternativas si hay disponibles."""

    _RX_FALLBACK_MARCA = re.compile(
        r"\bpref(?:iero|er[ií]a|erible)\s+\w+"
        r"|\bm[ií]\s+(?:marca\s+)?(?:preferida|favorita|de\s+confianza)\s+es\s+\w+"
        r"|\b(?:samsung|apple|xiaomi|sony|hp|dell|lenovo|asus|lg)\b[^.;]{0,40}"
        r"\b(?:pero|aunque)\s+(?:acepto|tambi[eé]n|me\s+sirve|esta\s+bien)\b"
        r"|\bsi\s+no\s+hay\s+\w+\s*(?:,|me\s+sirve|esta\s+bien)\b",
        re.IGNORECASE,
    )

    @classmethod
    def renderizar(cls, mensaje: str) -> str | None:
        if not mensaje or not cls._RX_FALLBACK_MARCA.search(mensaje):
            return None
        return (
            "FALLBACK DE MARCA: el cliente prefirio una marca pero acepta "
            "alternativas. Si NO hay stock de la marca preferida, en la respuesta:\n"
            "  1. Avisar explicitamente: 'No encontre <marca preferida> disponible.'\n"
            "  2. Para CADA alternativa citada, comparar con el criterio que "
            "el cliente declaro (almacenamiento, camara, RAM, etc) y advertir "
            "si NO cumple alguno: 'tiene 128GB, no 256GB que pediste — si "
            "priorizas almacenamiento, mira esta otra'.\n"
            "  3. Mostrar al menos 2 alternativas distintas si hay stock — no "
            "una sola opcion."
        )
