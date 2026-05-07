from __future__ import annotations

import re
from typing import Optional
from uuid import UUID

from ..commands.actualizar_perfil_sesion import ActualizarPerfilSesionCommand
from ..queries.resolver_categoria_sinonimo import (
    ResolverCategoriaSinonimoHandler,
    ResolverCategoriaSinonimoQuery,
)
from .detector_exclusiones_mensaje import DetectorExclusionesMensaje
from .detector_genero_mencion import DetectorGeneroMencion
from .detector_gpu_dedicada import DetectorGpuDedicada
from .detector_sku_mensaje import DetectorSkuMensaje
from .detector_requisitos_obligatorios import DetectorRequisitosObligatorios
from .detector_tier_deseado import DetectorTierDeseado
from .detector_uso_tecnico import DetectorUsoTecnico
from .extractor_atributos_mensaje import ExtractorAtributosMensaje
from .parser_presupuesto import ParserPresupuesto
from .sanitizador_query_busqueda import SanitizadorQueryBusqueda

RX_MARCAS = re.compile(
    r"\b(acer|asus|hp|lenovo|dell|apple|samsung|lg|sony|xiaomi|huawei|"
    r"motorola|nokia|microsoft|msi|gigabyte|bosch|philips|panasonic|"
    r"whirlpool|electrolux|daewoo|oster|black\s*\+?\s*decker|recco|"
    r"haceb|indurama|mabe|tcl|hisense|jvc|sankey|kalley)\b",
    re.IGNORECASE,
)
RX_USO = re.compile(
    r"\b(gaming|juegos?|los\s+juegos|para\s+jugar|para\s+el\s+play|play\s+station|ps[45]|xbox|"
    r"dise[\xf1n]o\s+gr[a\xe1]fico|dise[\xf1n]o|edici[o\xf3]n\s+de\s+video|edici[o\xf3]n|"
    r"programaci[o\xf3]n|programar|docker|desarrollo|"
    r"oficina|estudio|estudiar|trabajo\s+pesado|trabajo|teletrabajo|chambear|chambeo|"
    r"streaming|cocina|hogar|para\s+la\s+casa|familia|regalo|"
    r"viaje|universidad|colegio|renderizado|fotograf[i\xed]a|m[u\xfa]sica|"
    r"ingenier[i\xed]a|autocad|civil\s*3d|solidworks|revit|render)\b",
    re.IGNORECASE,
)


class ExtractorPerfilMensaje:
    """SRP: extraer preferencias (presupuesto, marca, categoria, uso, specs)
    desde el mensaje del cliente y armar el ActualizarPerfilSesionCommand.

    Usa DetectorUsoTecnico para inferir specs mínimas desde usos profesionales
    (ej. 'AutoCAD' → ram_min=16, ssd_min=512). Acumula exclusiones detectadas."""

    def __init__(self, resolver: ResolverCategoriaSinonimoHandler) -> None:
        self._resolver = resolver

    def extraer(self, sesion_id: UUID, mensaje: str) -> ActualizarPerfilSesionCommand:
        texto = (mensaje or "").strip()
        atributos = ExtractorAtributosMensaje.extraer(texto)
        categoria, subcategoria, sku_foco = self._resolver_entidad(texto)
        # Si el cliente menciona un SKU explícito (ej. [ACE-NHU1PAA001] o
        # ACE-NHU1PAA001 pelado), gana sobre lo que devolvió el resolver
        # de sinónimos: es el ancla más fuerte para los siguientes turnos.
        sku_explicito = DetectorSkuMensaje.extraer(texto)
        if sku_explicito:
            sku_foco = sku_explicito

        # Inferir specs mínimas desde uso técnico declarado
        uso_specs = DetectorUsoTecnico.detectar(texto)
        ram_min = atributos.ram_gb_min or (uso_specs.ram_gb_min if uso_specs else None)
        ssd_min = atributos.ssd_gb_min or (uso_specs.ssd_gb_min if uso_specs else None)

        # GPU: explícita en el mensaje o requerida por uso técnico
        gpu = True if DetectorGpuDedicada.requiere_gpu(texto) else None
        if gpu is None and uso_specs and uso_specs.gpu_requerida:
            gpu = True

        # Exclusiones del turno actual (explícitas + implícitas por uso)
        excluye_turno: list[str] = [*DetectorExclusionesMensaje.detectar(texto)]
        if uso_specs and uso_specs.excluir_nombres:
            excluye_turno = [*{*excluye_turno, *uso_specs.excluir_nombres}]
        nombre_excluye_nuevas = ",".join(excluye_turno) if excluye_turno else None

        ideal, techo = self._presupuesto_rango(texto)
        return ActualizarPerfilSesionCommand(
            sesion_id=sesion_id,
            presupuesto_max=techo,
            presupuesto_ideal=ideal,
            marca_preferida=self._marca(texto),
            categoria_foco=categoria,
            subcategoria_foco=subcategoria,
            sku_foco=sku_foco,
            genero_declarado=DetectorGeneroMencion.detectar(texto),
            desired_tier=DetectorTierDeseado.detectar(texto),
            uso_declarado=self._uso(texto),
            pulgadas=atributos.pulgadas,
            tipo_panel=atributos.tipo_panel,
            resolucion=atributos.resolucion,
            ram_gb_min=ram_min,
            gpu_dedicada=gpu,
            ssd_gb_min=ssd_min,
            nombre_excluye_nuevas=nombre_excluye_nuevas,
        )

    @staticmethod
    def _presupuesto(texto: str) -> float | None:
        if DetectorRequisitosObligatorios.precio_es_preferible(texto):
            return None
        return ParserPresupuesto.extraer(texto)

    @staticmethod
    def _presupuesto_rango(texto: str) -> tuple[float | None, float | None]:
        if DetectorRequisitosObligatorios.precio_es_preferible(texto):
            return None, None
        return ParserPresupuesto.extraer_rango(texto)

    @staticmethod
    def _marca(texto: str) -> str | None:
        match = RX_MARCAS.search(texto)
        return match.group(1).strip().lower() if match else None

    _CANONICO_USO: dict[str, str] = {
        "para el play": "gaming", "play station": "gaming",
        "ps4": "gaming", "ps5": "gaming", "xbox": "gaming",
        "juego": "gaming", "juegos": "gaming", "los juegos": "gaming",
        "para jugar": "gaming",
        "docker": "programacion", "desarrollo": "programacion", "programar": "programacion",
        "chambear": "oficina", "chambeo": "oficina", "teletrabajo": "oficina",
        "trabajo pesado": "oficina", "trabajo": "oficina",
        "estudiar": "estudio",
        "edicion": "diseno", "edicion de video": "diseno",
        "ingenieria": "ingenieria", "autocad": "ingenieria", "civil 3d": "ingenieria",
        "solidworks": "ingenieria", "revit": "ingenieria",
        "renderizado": "diseno", "render": "diseno",
    }

    @classmethod
    def _uso(cls, texto: str) -> str | None:
        match = RX_USO.search(texto)
        if not match:
            return None
        raw = match.group(1).lower()
        return cls._CANONICO_USO.get(raw, raw)

    def _resolver_entidad(
        self, texto: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Resuelve (categoria, subcategoria, sku) desde el texto.

        Estrategia en cascada:
        1. Si el sanitizador acepta la frase, intenta resolver completa.
        2. Si no, fragmenta por palabras significativas y prueba la primera
           que matchee. Esto evita que mensajes largos conversacionales
           ('hola, quiero una laptop bueno en realidad para mi hermano...')
           queden sin categoría — donde 'laptop' está claramente presente
           pero el sanitizador rechaza la frase entera por las stopwords.
        """
        if not texto:
            return None, None, None
        # Intento 1: frase completa (si pasa el sanitizador)
        if SanitizadorQueryBusqueda.sanitizar(texto) is not None:
            resultado = self._resolver.ejecutar(
                ResolverCategoriaSinonimoQuery(texto=texto, limite_relaciones=0)
            )
            sin = resultado.sinonimo_directo
            if sin is not None:
                return sin.categoria, sin.subcategoria, sin.sku_especifico
        # Intento 2: token por token, filtrando negaciones explícitas.
        return self._resolver_por_tokens(texto)

    def _resolver_por_tokens(
        self, texto: str
    ) -> tuple[Optional[str], Optional[str], Optional[str]]:
        """Recorre las palabras significativas del texto y devuelve la
        primera que el resolver identifica como sinónimo del catálogo.

        Filtra palabras que vienen después de un negador en la misma
        cláusula ('no quiero chromebook', 'tampoco celeron') para que
        esas palabras NO se usen como categoría positiva."""
        tokens = self._tokens_significativos(texto)
        for token in tokens:
            try:
                resultado = self._resolver.ejecutar(
                    ResolverCategoriaSinonimoQuery(texto=token, limite_relaciones=0)
                )
            except Exception:
                continue
            sin = resultado.sinonimo_directo
            if sin is not None:
                return sin.categoria, sin.subcategoria, sin.sku_especifico
        return None, None, None

    # Stopwords que NO son nombres de producto/categoría — se filtran.
    _STOPWORDS_TOKENIZER = frozenset({
        "hola", "buenos", "buenas", "dias", "tardes", "noches",
        "quiero", "queria", "necesito", "busco", "buscar", "tengo",
        "para", "por", "con", "sin", "una", "uno", "del", "los", "las",
        "este", "esta", "esto", "ese", "esa", "eso", "que", "como",
        "donde", "cuando", "porque", "porqué", "porque", "cual",
        "muy", "mas", "más", "menos", "mucho", "poco", "tampoco",
        "bueno", "buena", "mejor", "peor", "mismo", "misma",
        "realidad", "realmente", "creo", "pienso", "supongo",
        "hermano", "hermana", "mama", "papa", "amigo", "novio",
        "la", "el", "le", "lo", "se", "te", "me", "nos",
        "mi", "tu", "su", "es", "ya", "ahora", "hoy", "mañana",
        "estudiar", "estudia", "estudios",  # son uso, no producto
        "ingenieria", "ingeniería", "ingeniero", "civil", "industrial",
        "medicina", "carrera", "universidad", "u", "colegio",
        "programa", "programas", "pesados", "pesado",
        "puedo", "puede", "podes", "podes", "ayudar",
        "carisimo", "barato", "caro", "precio", "presupuesto",
        "minimo", "mínimo", "máximo", "maximo",
        "ram", "gb", "tb", "mb", "ghz", "hz", "watts", "mah",
        "dame", "dime", "decime",
        "explicame", "explica", "explíca", "explicar", "explicaci",
        "alguien", "sabe", "sabes",
        "compus", "computacion",  # ambiguo, mejor exigir "laptop/notebook"
        "opciones", "opcion", "ficha", "specs",
    })

    # Negadores: si una palabra del catálogo viene después de uno de
    # estos en la misma cláusula, se descarta como detección positiva.
    _RX_CLAUSULA_NEGADA = re.compile(
        r"(?:^|[.,;]|\b)(?:no\s+(?:quiero|me\s+gusta|me\s+interesa|"
        r"me\s+sirve|necesito|busco)|tampoco|nada\s+de|excepto|"
        r"sin|menos\s+que\s+sea|que\s+no\s+sea|odio|detesto|"
        r"jam[áa]s)\b[^.,;]*",
        re.IGNORECASE,
    )

    @classmethod
    def _tokens_significativos(cls, texto: str) -> list[str]:
        """Tokens que pueden ser candidato a producto: ≥4 chars, no stopword,
        no dentro de cláusula negada. Devuelve en orden de aparición."""
        if not texto:
            return []
        # Marca rangos de cláusulas negadas para excluir tokens en ese span
        rangos_negados = [
            (m.start(), m.end()) for m in cls._RX_CLAUSULA_NEGADA.finditer(texto)
        ]
        tokens: list[str] = []
        for m in re.finditer(r"\b[A-Za-zÁÉÍÓÚáéíóúÑñ]{4,}\b", texto):
            posicion = m.start()
            palabra = m.group(0).lower()
            if palabra in cls._STOPWORDS_TOKENIZER:
                continue
            if any(ini <= posicion < fin for ini, fin in rangos_negados):
                continue
            tokens.append(palabra)
        return tokens
