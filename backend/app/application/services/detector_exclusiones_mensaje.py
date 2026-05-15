from __future__ import annotations

import re
from typing import Iterable

from ...domain.shared.normalizacion import NormalizadorTexto
from .matcher_fuzzy_keywords import MatcherFuzzyKeywords


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
        # Electrodomésticos de refrigeración excluibles explícitamente
        "conservadora", "minibar", "exhibidor", "vitrina",
        # Procesadores/componentes low-end — excluibles cuando el cliente los pide explícitamente
        "celeron", "pentium", "chromebook",
    )

    # Regex para detectar componentes técnicos no deseados citados explícitamente
    # en un contexto de exclusión (lista tras "no me muestres", "no quiero", etc.)
    _RX_TECH_NEGADA = re.compile(
        r"\b(?:no\s+(?:me\s+)?(?:quiero|muestres?|incluyas?|pongas?)\s+[^.;]*?|"
        r"(?:nada\s+de|sin|excluye)\s*[^.;]*?)\b"
        r"(celeron|pentium|chromebook)\b",
        re.IGNORECASE,
    )
    _DISTANCIA_MAX = 1

    # Trigger de negacion tolerante a typos: "no quiero", "no qiero", "no kiero",
    # "tampoko", etc. La parte gatillo se detecta SOLO via regex; la palabra
    # negada (group 1) se valida despues con fuzzy match contra el diccionario.
    _RX_NEGACION = re.compile(
        r"\b(?:"
        r"menos\s+que\s+sea|que\s+no\s+sea|nada\s+de|tampoco|tampoko"
        r"|no\s+(?:lo\s+)?(?:quiero|qiero|kiero|quero|kero|kiero|deseo|"
        r"muestres?|incluyas?|pongas?|necesito|nesesito|busco)\s+(?:una?\s+|el\s+|la\s+|ver\s+|que\s+sea\s+)?"
        r"|pero\s+no\s+(?:una?\s+|el\s+|la\s+)?"
        r"|sino\s+(?:una?\s+|el\s+|la\s+)?"
        r"|excepto\s+(?:una?\s+|el\s+|la\s+)?"
        r"|no\s+una?\s+|menos|sin|no\s+"
        r")"
        r"([a-zñáéíóúü]{3,})",
        re.IGNORECASE,
    )

    # Captura de listas tras un trigger de negacion ("no quiero X ni Y ni Z").
    # Devuelve el segmento entero hasta el siguiente punto/coma fuerte para
    # que se escanee con fuzzy contra el diccionario. Tolera 'me'/'lo' entre
    # 'no' y el verbo ("no me muestres", "no lo quiero").
    _RX_NEGACION_BLOQUE = re.compile(
        r"\b(?:no\s+(?:me\s+|lo\s+|la\s+)?(?:quiero|qiero|kiero|quero|kero|deseo|"
        r"muestres?|incluyas?|pongas?|necesito|nesesito|busco|deseas?)|"
        r"tampoco|tampoko|nada\s+de|sin\s+|excepto|excluye)\b([^.;]+)",
        re.IGNORECASE,
    )

    # Por keyword detectado en el mensaje, excluir estas variantes del nombre
    # si NO aparece ninguna señal positiva que las pida explícitamente.
    _EXCLUSIONES_IMPLICITAS: dict[str, tuple[tuple[str, ...], tuple[str, ...]]] = {
        # keyword gatillo    → (exclusiones si no está el "anti-keyword"    ,  anti-keywords)
        "reloj":  (("pared", "mural", "cocina"),  ("pared", "mural", "cocina", "decorativo")),
        # Uso profesional → excluir procesadores de entrada del nombre
        "ingenieria": (("celeron", "pentium"), ("celeron", "pentium")),
        "autocad":    (("celeron", "pentium"), ("celeron", "pentium")),
        "solidworks": (("celeron", "pentium"), ("celeron", "pentium")),
        "render":     (("celeron", "pentium"), ("celeron", "pentium")),
        "renderizado": (("celeron", "pentium"), ("celeron", "pentium")),
        # Refrigeradora doméstica → excluir herméticos/recipientes/enfriadores CPU.
        # "cpu" excluye "Refrigerador de CPU Forza 85" que el DB agrupa bajo refrigeración.
        # "conservadora"/"frigobar"/"freezer" excluyen por nombre cuando tipo_producto es NULL.
        "refrigeradora": (
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor"),
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor", "comercial"),
        ),
        "refrigerador": (
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor"),
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor", "comercial"),
        ),
        "refri": (
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor"),
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor", "comercial"),
        ),
        "heladera": (
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor"),
            ("hermetico", "tupper", "recipiente", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor", "comercial"),
        ),
        # Nombre de categoria BD — para follow-ups sin mensaje original.
        # Incluye "pote"/"tarro" y "cpu" para excluir tarros y enfriadores de CPU.
        "refrigeracion": (
            ("hermetico", "tupper", "recipiente", "pote", "tarro", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor"),
            ("hermetico", "tupper", "recipiente", "pote", "tarro", "cpu", "conservadora", "frigobar", "freezer", "minibar", "exhibidor", "comercial"),
        ),
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
        # 'refri/refrigerador/refrigeradora' por default = principal de cocina;
        # excluimos exhibidores comerciales, freezers horizontales, frigobars
        # y minibars salvo que el cliente los pida explicitamente.
        "refri": (
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora"),
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora", "comercial", "negocio", "tienda"),
        ),
        "refrigerador": (
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora"),
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora", "comercial", "negocio", "tienda"),
        ),
        "refrigeradora": (
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora"),
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora", "comercial", "negocio", "tienda"),
        ),
        "heladera": (
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora"),
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora", "comercial", "negocio", "tienda"),
        ),
        # 'lavadora' por default = principal de hogar; excluimos secadoras
        # solas y centros de lavado mini.
        "lavadora": (
            ("secadora", "centro_lavado_mini"),
            ("secadora", "secado", "centro", "compacta"),
        ),
        # Variantes con nombre de categoria BD (ej: categoria_foco en perfil).
        # Permiten que follow-ups (otra opcion, mas barato) apliquen los mismos
        # filtros sin tener el mensaje original — basta con perfil.categoria_foco.
        "refrigeracion": (
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora"),
            ("frigobar", "minibar", "freezer", "exhibidor", "vitrina", "conservadora", "comercial", "negocio", "tienda"),
        ),
        "lavado": (
            ("secadora", "centro_lavado_mini"),
            ("secadora", "secado", "centro", "compacta"),
        ),
        "relojeria": (
            ("pared", "despertador", "decorativo"),
            ("pared", "despertador", "decorativo"),
        ),
        "impresion": (
            ("impresora_termica",),
            ("termica", "termicas", "pos", "recibos", "etiquetas", "etiqueta"),
        ),
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
            *cls._componentes_tech_negados(norm),
        })

    # Solo estos terminos low-end aceptan fuzzy en el escaneo post-negacion.
    # Los otros (colores, partes) requieren match exacto para evitar falsos
    # positivos cuando el cliente menciona algo neutro ('rojo' como adjetivo).
    _TECH_FUZZY = ("celeron", "pentium", "chromebook")

    # Umbral mas permisivo para tech keywords ('chrombuk' -> 'chromebook' tiene
    # ratio ~0.778, debajo del 0.78 default). Diccionario chico + alto recall
    # justifican bajar a 0.74 sin riesgo de falso positivo.
    _RATIO_TECH = 0.74

    @classmethod
    def _componentes_tech_negados(cls, norm: str) -> list[str]:
        """Captura procesadores/componentes low-end citados en lista tras señal de exclusión.
        Cubre 'no me muestres Celeron, Pentium' y typos como 'chrombuk' o 'celeron'."""
        salida: list[str] = []
        for m in cls._RX_TECH_NEGADA.finditer(norm):
            salida.append(m.group(1).lower())
        # Tras un trigger de negacion ('no quiero/qiero/kiero...'), escanear
        # cada palabra del bloque hasta el siguiente punto/coma y matchear
        # con fuzzy contra _TECH_FUZZY.
        for m in cls._RX_NEGACION_BLOQUE.finditer(norm):
            for palabra in re.findall(r"[a-zñáéíóúü]{4,}", m.group(1)):
                match = MatcherFuzzyKeywords.mejor_match(
                    palabra, cls._TECH_FUZZY, ratio_min=cls._RATIO_TECH,
                )
                if match and match not in salida:
                    salida.append(match)
        return salida

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
        # Captura 1: una palabra por trigger ("no quiero X", "sin X")
        for m in cls._RX_NEGACION.finditer(norm):
            corregido = cls._corregir_typo(m.group(1))
            if corregido and corregido not in salida:
                salida.append(corregido)
        # Captura 2: bloque completo tras trigger — cubre "no me muestres: -
        # frigobar - minibar - freezer" y listas con colon/guiones que el
        # regex puntual no detecta. Escanea cada palabra del bloque contra
        # el diccionario tolerante.
        for m in cls._RX_NEGACION_BLOQUE.finditer(norm):
            for palabra in re.findall(r"[a-zñáéíóúü]{4,}", m.group(1)):
                corregido = cls._corregir_typo(palabra)
                if corregido and corregido not in salida:
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
        """Mapea 'pered' -> 'pared' buscando la palabra del diccionario con
        match fuzzy (Levenshtein 1 + ratio fonetico para typos mayores como
        'chrombuk' -> 'chromebook'). Devuelve la palabra canonica si hay
        match razonable, None si no."""
        p = palabra.lower()
        if p in cls._DICCIONARIO_TOLERANTE:
            return p
        # Levenshtein 1 — barato y preciso para typos chicos.
        for candidato in cls._DICCIONARIO_TOLERANTE:
            if cls._distancia(p, candidato) <= cls._DISTANCIA_MAX:
                return candidato
        # Si la palabra es lo suficientemente larga (≥ 6 chars), tolerar
        # typos mayores con fuzzy fonetico — captura 'chrombuk'/'chromebok'.
        if len(p) >= 6:
            return MatcherFuzzyKeywords.mejor_match(p, cls._DICCIONARIO_TOLERANTE)
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
