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
    r"\b(gaming|juegos?|disenio|disẽno|programaci?on|programar|"
    r"oficina|estudio|estudiar|trabajo|teletrabajo|edicion|edicion de video|"
    r"streaming|cocina|hogar|familia|regalo|viaje|universidad|colegio)\b",
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
        categoria, subcategoria = self._categoria_y_subcategoria(texto)
        return ActualizarPerfilSesionCommand(
            sesion_id=sesion_id,
            presupuesto_max=self._presupuesto(texto),
            marca_preferida=self._marca(texto),
            categoria_foco=categoria,
            subcategoria_foco=subcategoria,
            genero_declarado=DetectorGeneroMencion.detectar(texto),
            uso_declarado=self._uso(texto),
            pulgadas=atributos.pulgadas,
            tipo_panel=atributos.tipo_panel,
            resolucion=atributos.resolucion,
        )

    @staticmethod
    def _presupuesto(texto: str) -> float | None:
        return ParserPresupuesto.extraer(texto)

    @staticmethod
    def _marca(texto: str) -> str | None:
        match = RX_MARCAS.search(texto)
        return match.group(1).strip().lower() if match else None

    @staticmethod
    def _uso(texto: str) -> str | None:
        match = RX_USO.search(texto)
        return match.group(1).lower() if match else None

    def _categoria_y_subcategoria(
        self, texto: str
    ) -> tuple[Optional[str], Optional[str]]:
        if not texto:
            return None, None
        resultado = self._resolver.ejecutar(
            ResolverCategoriaSinonimoQuery(texto=texto, limite_relaciones=0)
        )
        sin = resultado.sinonimo_directo
        if sin is None:
            return None, None
        return sin.categoria, sin.subcategoria
