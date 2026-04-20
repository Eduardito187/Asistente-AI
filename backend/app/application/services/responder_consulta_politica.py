from __future__ import annotations

import re

from .respuesta_follow_up import RespuestaFollowUp


class ResponderConsultaPolitica:
    """SRP: responder determinsticamente consultas de politica comercial
    (envio, garantia, tiempo de entrega, financiamiento, cuotas, sucursal).
    Estas preguntas no dependen de un producto: respuesta canonica y corta
    que invita a seguir la venta.

    Lo que NO maneja (delegamos al LLM porque requieren contexto de producto):
      - Consulta de stock puntual
      - Consulta de precio puntual

    Estrategia: regex deterministas, sin LLM. Si ninguna aplica, devuelve
    None y el turno cae al flujo normal."""

    _PATRONES: tuple[tuple[str, re.Pattern[str]], ...] = (
        (
            "garantia",
            re.compile(
                r"\b(garant[ií]a|tiene\s+garant[ií]a|cu[aá]nto\s+de\s+garant[ií]a)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "tiempo_entrega",
            re.compile(
                r"\b(cuanto\s+(?:tarda|demora)|tiempo\s+de\s+entrega|"
                r"cu[aá]ndo\s+(?:llega|me\s+llega)|tarda\s+mucho|"
                r"demora\s+(?:mucho|cuanto))\b",
                re.IGNORECASE,
            ),
        ),
        (
            "envio",
            re.compile(
                r"\b(hacen\s+env[ií]os?|env[ií]an|delivery|"
                r"env[ií]o\s+a|mandan\s+a|llevan\s+a\s+domicilio)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "financiamiento",
            re.compile(
                r"\b(financiamiento|financiar|a\s+cr[eé]dito|"
                r"planes?\s+de\s+pago)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "cuotas",
            re.compile(
                r"\b(cuotas?|en\s+cuotas|a\s+plazos|pago\s+diferido)\b",
                re.IGNORECASE,
            ),
        ),
        (
            "sucursal",
            re.compile(
                r"\b(sucursal(?:es)?|en\s+que\s+tienda|d[oó]nde\s+(?:queda|est[aá]\s+la)|"
                r"qu[eé]\s+local|en\s+qu[eé]\s+ciudad\s+(?:tienen|est[aá]n))\b",
                re.IGNORECASE,
            ),
        ),
    )

    _RESPUESTAS: dict[str, str] = {
        "garantia": (
            "Todos nuestros productos tienen garantía oficial del fabricante "
            "(minimo 1 año, varia segun categoria). Si queres te confirmo la "
            "garantia exacta de un producto puntual — decime cual te interesa."
        ),
        "tiempo_entrega": (
            "El tiempo de entrega depende de tu ciudad: en La Paz y ciudades "
            "principales solemos entregar en 24-48h, al resto de Bolivia en "
            "2-5 dias habiles. ¿A donde te lo enviamos?"
        ),
        "envio": (
            "Si, hacemos envios a todo Bolivia. El costo y tiempo depende de "
            "la ciudad — decime a donde lo mandamos y te paso el detalle."
        ),
        "financiamiento": (
            "Si, manejamos planes de financiamiento. Podemos armar cuotas con "
            "tarjeta o credito directo segun el producto. ¿Cual te interesa y "
            "en cuantas cuotas lo pensabas?"
        ),
        "cuotas": (
            "Si, podes pagar en cuotas con tarjetas de credito de los bancos "
            "principales. El plan (3, 6, 12 cuotas) depende de tu banco. ¿Que "
            "producto queres y en cuantas cuotas lo pensas?"
        ),
        "sucursal": (
            "Tenemos sucursales en La Paz, Santa Cruz, Cochabamba y otras "
            "ciudades. ¿Desde que ciudad consultas? Te indico la sucursal mas "
            "cercana y el stock que tiene."
        ),
    }

    @classmethod
    def responder(cls, mensaje: str) -> RespuestaFollowUp | None:
        if not mensaje:
            return None
        for clave, rx in cls._PATRONES:
            if rx.search(mensaje):
                return RespuestaFollowUp(
                    texto=cls._RESPUESTAS[clave],
                    productos=[],
                    skus=[],
                    ruta=f"consulta_politica_{clave}",
                )
        return None
