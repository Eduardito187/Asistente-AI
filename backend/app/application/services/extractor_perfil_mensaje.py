from __future__ import annotations

import re
from uuid import UUID

from ..commands.actualizar_perfil_sesion import ActualizarPerfilSesionCommand
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
    r"\b(gaming|juegos?|disenio|disen\u0303o|programaci?on|programar|"
    r"oficina|estudio|estudiar|trabajo|teletrabajo|edicion|edicion de video|"
    r"streaming|cocina|hogar|familia|regalo|viaje|universidad|colegio)\b",
    re.IGNORECASE,
)
RX_CATEGORIAS = {
    "Laptops": re.compile(
        r"\b(laptop|notebook|portatil|ultrabook|macbook)\b", re.IGNORECASE,
    ),
    "Celulares": re.compile(
        r"\b(celular|smartphone|telefono|iphone|movil)\b", re.IGNORECASE,
    ),
    "Televisores": re.compile(
        r"\b(tv|televisor|smart\s*tv|pantalla|tele)\b", re.IGNORECASE,
    ),
    "Electrodomesticos": re.compile(
        r"\b(freidora|licuadora|lavadora|secadora|refrigerador|heladera|nevera|"
        r"microondas|horno|cocina|aspiradora|ventilador|aire\s+acondicionado|"
        r"batidora|cafetera|tostadora|plancha)\b",
        re.IGNORECASE,
    ),
    "Audio": re.compile(
        r"\b(audifonos|auriculares|parlante|bocina|soundbar|"
        r"barra\s+de\s+sonido|home\s*theater)\b",
        re.IGNORECASE,
    ),
    "Computacion": re.compile(
        r"\b(pc|desktop|monitor|teclado|mouse|impresora|raton)\b",
        re.IGNORECASE,
    ),
}


class ExtractorPerfilMensaje:
    """SRP: extraer preferencias (presupuesto, marca, categoria, uso) desde el
    mensaje del cliente y armar el ActualizarPerfilSesionCommand.

    Usa solo regex — es determinista, sin LLM, y solo persiste lo que el
    cliente DECLARO explicitamente."""

    def extraer(self, sesion_id: UUID, mensaje: str) -> ActualizarPerfilSesionCommand:
        texto = (mensaje or "").strip()
        atributos = ExtractorAtributosMensaje.extraer(texto)
        return ActualizarPerfilSesionCommand(
            sesion_id=sesion_id,
            presupuesto_max=self._presupuesto(texto),
            marca_preferida=self._marca(texto),
            categoria_foco=self._categoria(texto),
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

    @staticmethod
    def _categoria(texto: str) -> str | None:
        for nombre, rx in RX_CATEGORIAS.items():
            if rx.search(texto):
                return nombre
        return None
