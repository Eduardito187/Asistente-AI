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
        r"\b(laptops?|notebooks?|portatiles?|portatil|ultrabooks?|macbooks?)\b",
        re.IGNORECASE,
    ),
    "Celulares": re.compile(
        r"\b(celulares?|smartphones?|telefonos?|iphones?|moviles?|movil|celu|celus)\b",
        re.IGNORECASE,
    ),
    "Televisores": re.compile(
        r"\b(tv|tvs|televisor(?:es)?|smart\s*tv|pantallas?|teles?)\b",
        re.IGNORECASE,
    ),
    "Electrodomesticos": re.compile(
        r"\b(freidoras?|licuadoras?|lavadoras?|secadoras?|refrigeradores?|"
        r"refrigerador|heladeras?|neveras?|microondas|hornos?|cocinas?|"
        r"aspiradoras?|ventiladores?|ventilador|aire\s+acondicionado|"
        r"batidoras?|cafeteras?|tostadoras?|planchas?)\b",
        re.IGNORECASE,
    ),
    "Audio": re.compile(
        r"\b(audifonos?|auriculares?|parlantes?|bocinas?|soundbars?|"
        r"barra\s+de\s+sonido|home\s*theater)\b",
        re.IGNORECASE,
    ),
    "Computacion": re.compile(
        r"\b(pc|pcs|desktops?|monitores?|monitor|teclados?|mouse|ratones?|raton|"
        r"impresoras?)\b",
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
