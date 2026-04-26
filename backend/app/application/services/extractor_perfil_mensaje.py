from __future__ import annotations

import re
from typing import Optional
from uuid import UUID

from ..commands.actualizar_perfil_sesion import ActualizarPerfilSesionCommand
from ..queries.resolver_categoria_sinonimo import (
    ResolverCategoriaSinonimoHandler,
    ResolverCategoriaSinonimoQuery,
)
from .detector_genero_mencion import DetectorGeneroMencion
from .detector_gpu_dedicada import DetectorGpuDedicada
from .detector_tier_deseado import DetectorTierDeseado
from .extractor_atributos_mensaje import ExtractorAtributosMensaje
from .parser_presupuesto import ParserPresupuesto

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
    r"viaje|universidad|colegio|renderizado|fotograf[i\xed]a|m[u\xfa]sica)\b",
    re.IGNORECASE,
)


class ExtractorPerfilMensaje:
    """SRP: extraer preferencias (presupuesto, marca, categoria, uso) desde el
    mensaje del cliente y armar el ActualizarPerfilSesionCommand.

    La categoria/subcategoria se resuelve contra la tabla `categorias_sinonimos`
    via ResolverCategoriaSinonimoHandler — asi el vocabulario es data-driven y
    cubre todo el catalogo (Smartwatch, Relojeria, Cocina Menor, etc.) sin
    tocar codigo."""

    def __init__(self, resolver: ResolverCategoriaSinonimoHandler) -> None:
        self._resolver = resolver

    def extraer(self, sesion_id: UUID, mensaje: str) -> ActualizarPerfilSesionCommand:
        texto = (mensaje or "").strip()
        atributos = ExtractorAtributosMensaje.extraer(texto)
        categoria, subcategoria, sku_foco = self._resolver_entidad(texto)
        return ActualizarPerfilSesionCommand(
            sesion_id=sesion_id,
            presupuesto_max=self._presupuesto(texto),
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
            ram_gb_min=atributos.ram_gb_min,
            gpu_dedicada=True if DetectorGpuDedicada.requiere_gpu(texto) else None,
        )

    @staticmethod
    def _presupuesto(texto: str) -> float | None:
        return ParserPresupuesto.extraer(texto)

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
        """Resuelve el texto del cliente contra categorias_sinonimos y devuelve
        (categoria, subcategoria, sku_especifico). Si el alias identifica un
        producto concreto (ej. 's26 ultra'), sku_especifico != None; si apunta
        solo a una categoria (ej. 'celular'), sku es None."""
        if not texto:
            return None, None, None
        resultado = self._resolver.ejecutar(
            ResolverCategoriaSinonimoQuery(texto=texto, limite_relaciones=0)
        )
        sin = resultado.sinonimo_directo
        if sin is None:
            return None, None, None
        return sin.categoria, sin.subcategoria, sin.sku_especifico
