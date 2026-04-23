from __future__ import annotations

import re
from typing import Iterable

from ...domain.shared.normalizacion import NormalizadorTexto


class DetectorExclusionesMensaje:
    """SRP: extrae del mensaje del cliente keywords que deben quedar
    EXCLUIDAS del nombre de los productos devueltos.

    Dos orígenes:

      1) Negación explícita: "no para pared", "que no sea rojo", "menos que
         sea de cocina". Captura el sustantivo que sigue a la negación.
         Tolera typos leves (Levenshtein 1) contra un pequeño diccionario
         para que "pered" → "pared".

      2) Exclusión implícita por query ambigua: cuando el cliente dice
         solo "reloj" (sin calificar "de pared" o "inteligente"), el
         catálogo mezcla pulsera y pared bajo la misma subcategoría. Por
         default interpretamos reloj = pulsera, y excluimos pared/mural
         del nombre. Si el cliente dice explícitamente "reloj de pared",
         esa exclusión NO se aplica.
    """

    # keywords a buscar/negar — pensadas por la escasez de subcategorías
    # finas en el catálogo (no hay "reloj pulsera" vs "reloj pared").
    _DICCIONARIO_TOLERANTE = (
        "pared", "mural", "cocina", "pulsera", "muneca",
        "rojo", "negro", "blanco", "azul", "rosa",
    )
    _DISTANCIA_MAX = 1

    _RX_NEGACION = re.compile(
        r"\b(?:menos\s+que\s+sea|que\s+no\s+sea|nada\s+de|tampoco|menos|sin|no)"
        r"\s+(?:para\s+|sea\s+|de\s+)?([a-zñáéíóúü]{4,})",
        re.IGNORECASE,
    )

    # Por keyword detectado en el mensaje, excluir estas variantes del nombre
    # si NO aparece ninguna señal positiva que las pida explícitamente.
    _EXCLUSIONES_IMPLICITAS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        # keyword gatillo    → (exclusiones si no está el "anti-keyword"    ,  anti-keywords)
        "reloj":  (("pared", "mural", "cocina"),  ("pared", "mural", "cocina", "decorativo")),
    }

    @classmethod
    def detectar(cls, mensaje: str | None) -> list[str]:
        if not mensaje:
            return []
        norm = NormalizadorTexto.normalizar(mensaje)
        negadas = cls._negaciones_explicitas(norm)
        return sorted({
            *negadas,
            *cls._exclusiones_implicitas(norm, palabras_negadas=set(negadas)),
        })

    @classmethod
    def _negaciones_explicitas(cls, norm: str) -> list[str]:
        salida: list[str] = []
        for m in cls._RX_NEGACION.finditer(norm):
            palabra = m.group(1)
            corregido = cls._corregir_typo(palabra)
            if corregido:
                salida.append(corregido)
        return salida

    @classmethod
    def _exclusiones_implicitas(
        cls, norm: str, palabras_negadas: set[str]
    ) -> list[str]:
        """Las anti-keywords ("pared", "cocina"...) solo cancelan la exclusion
        implicita cuando aparecen POSITIVAS. Si el cliente dijo "menos de
        cocina", "cocina" entra por `palabras_negadas` y NO bloquea excluir
        pared/mural del reloj."""
        tokens = set(norm.split())
        salida: list[str] = []
        for gatillo, (excluir, anti) in cls._EXCLUSIONES_IMPLICITAS.items():
            if gatillo not in tokens:
                continue
            anti_positivas = [a for a in anti if a in norm and a not in palabras_negadas]
            if anti_positivas:
                # el cliente pidio explicitamente "reloj de pared" → no excluir
                continue
            salida.extend(excluir)
        return salida

    @classmethod
    def _corregir_typo(cls, palabra: str) -> str | None:
        """Mapea 'pered' → 'pared' buscando la palabra del diccionario con
        distancia de edición mínima. Devuelve la palabra canónica si está
        dentro del umbral; None si no hay match razonable."""
        p = palabra.lower()
        if p in cls._DICCIONARIO_TOLERANTE:
            return p
        for candidato in cls._DICCIONARIO_TOLERANTE:
            if cls._distancia(p, candidato) <= cls._DISTANCIA_MAX:
                return candidato
        return None

    @staticmethod
    def _distancia(a: str, b: str) -> int:
        """Levenshtein básico. Suficiente para typos de 1 carácter en
        palabras ≥ 4 chars."""
        if abs(len(a) - len(b)) > 1:
            return 99
        if a == b:
            return 0
        if len(a) > len(b):
            a, b = b, a
        # len(a) ≤ len(b), diferencia ≤ 1
        if len(a) == len(b):
            diffs = sum(ca != cb for ca, cb in zip(a, b))
            return diffs
        # len(b) == len(a) + 1 — buscamos una sola inserción
        for i in range(len(b)):
            if b[:i] + b[i + 1:] == a:
                return 1
        return 99
