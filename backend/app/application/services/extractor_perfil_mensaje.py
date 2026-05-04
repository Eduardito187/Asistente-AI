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
        if not texto:
            return None, None, None
        if SanitizadorQueryBusqueda.sanitizar(texto) is None:
            return None, None, None
        resultado = self._resolver.ejecutar(
            ResolverCategoriaSinonimoQuery(texto=texto, limite_relaciones=0)
        )
        sin = resultado.sinonimo_directo
        if sin is None:
            return None, None, None
        return sin.categoria, sin.subcategoria, sin.sku_especifico
