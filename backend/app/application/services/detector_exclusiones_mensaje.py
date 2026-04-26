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
        # Colores
        "rojo", "negro", "blanco", "azul", "rosa", "verde", "gris",
        # Partes y ubicaciones
        "pared", "mural", "cocina", "pulsera", "muneca",
        # Categorías de productos (para exclusión por tipo)
        "consola", "monitor", "parlante", "accesorio", "accesorios",
        "tablet", "laptop", "televisor", "celular", "impresora",
        "secadora", "frigobar", "freezer",
    )
    _DISTANCIA_MAX = 1

    _RX_NEGACION = re.compile(
        r"\b(?:"
        r"menos\s+que\s+sea|que\s+no\s+sea|nada\s+de|tampoco"
        r"|no\s+quiero\s+(?:una?\s+|el\s+|la\s+|ver\s+|que\s+sea\s+)?"
        r"|pero\s+no\s+(?:una?\s+|el\s+|la\s+)?"
        r"|sino\s+(?:una?\s+|el\s+|la\s+)?"
        r"|excepto\s+(?:una?\s+|el\s+|la\s+)?"
        r"|no\s+una?\s+|menos|sin|no\s+"
        r")"
        r"([a-zñáéíóúü]{3,})",
        re.IGNORECASE,
    )

    # Por keyword detectado en el mensaje, excluir estas variantes del nombre
    # si NO aparece ninguna señal positiva que las pida explícitamente.
    _EXCLUSIONES_IMPLICITAS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        # keyword gatillo    → (exclusiones si no está el "anti-keyword"    ,  anti-keywords)
        "reloj":  (("pared", "mural", "cocina"),  ("pared", "mural", "cocina", "decorativo")),
    }

    # Cuando el campo tipo_producto de la BD está poblado, este mapa indica
    # qué valores excluir para cada keyword gatillo.
    # NULL-safe: filas con tipo_producto NULL nunca quedan excluidas
    # (el SQL usa "tipo_producto IS NULL OR tipo_producto NOT IN (...)").
    _TIPOS_EXCLUIR: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        # keyword → (tipos a excluir, anti-keywords que cancelan la exclusión)
        "reloj": (("pared", "despertador", "decorativo"), ("pared", "despertador", "decorativo")),
        # Por default "impresora" busca la de hogar/oficina — excluimos las
        # térmicas (POS/recibos/etiquetas) salvo que el cliente lo pida.
        "impresora": (("impresora_termica",), ("termica", "termicas", "pos", "recibos", "etiquetas", "etiqueta")),
        "impresoras": (("impresora_termica",), ("termica", "termicas", "pos", "recibos", "etiquetas", "etiqueta")),
    }

    @classmethod
    def detectar(cls, mensaje: str | None) -> list[str]:
        if not mensaje:
            return []
        norm = NormalizadorTexto.normalizar(mensaje)
        negadas = cls._negaciones_explicitas(norm)
        return sorted({
            *negadas,
            *cls._calcular_exclusiones_implicitas(norm, palabras_negadas=set(negadas)),
        })

    @classmethod
    def tipos_a_excluir(cls, mensaje: str | None) -> list[str]:
        """Devuelve valores de tipo_producto a excluir de la búsqueda.

        Complementa detectar(): mientras ese opera sobre nombre_norm (texto),
        este opera sobre la columna tipo_producto cuando la BD la tiene poblada.
        La exclusión es NULL-safe en SQL: productos sin tipo_producto clasificado
        nunca quedan fuera — solo se filtran los que tienen el valor explícito."""
        if not mensaje:
            return []
        norm = NormalizadorTexto.normalizar(mensaje)
        tokens = set(norm.split())
        negadas = set(cls._negaciones_explicitas(norm))
        salida: list[str] = []
        for gatillo, (tipos, anti) in cls._TIPOS_EXCLUIR.items():
            if gatillo not in tokens:
                continue
            anti_positivas = [a for a in anti if a in norm and a not in negadas]
            if anti_positivas:
                continue
            salida.extend(tipos)
        return sorted(set(salida))

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
    def _calcular_exclusiones_implicitas(
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
