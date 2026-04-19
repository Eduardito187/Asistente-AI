from __future__ import annotations

import random
import re

from .intencion import Intencion
from .respuesta_intencion_directa import RespuestaIntencionDirecta

RX_SALUDO = re.compile(
    r"^\s*(hola|buenas|buenos dias|buenas tardes|buenas noches|hey|hi|que tal)\b[\s!.,:;\-]*$",
    re.IGNORECASE,
)
RX_DESPEDIDA = re.compile(
    r"^\s*(chau|chao|adios|hasta luego|nos vemos|bye|hasta pronto)\b[\s!.,:;\-]*$",
    re.IGNORECASE,
)
RX_GRACIAS = re.compile(
    r"^\s*(muchas gracias|gracias|mil gracias|perfecto|genial|excelente|listo)\b[\s!.,:;\-]*$",
    re.IGNORECASE,
)
RX_CARRITO = re.compile(
    r"\b(carrito|agregar al carrito|quitar del carrito|vaciar carrito|checkout|comprar)\b",
    re.IGNORECASE,
)
RX_PRODUCTO = re.compile(
    r"\b(laptop|notebook|celular|telefono|tv|televisor|freidora|licuadora|"
    r"refrigerador|heladera|lavadora|aire acondicionado|audifonos|parlante|"
    r"tablet|monitor|teclado|mouse|impresora|camara|consola|playstation|xbox|"
    r"modelo|marca|precio|stock|sku|catalogo)\b",
    re.IGNORECASE,
)

SALUDOS = (
    "Hola! Soy Dismi, tu asesor de Dismac. Que estas buscando hoy?",
    "Hola! En que te puedo ayudar? Podes pedirme productos, comparar precios o armar un carrito.",
    "Hey! Decime que necesitas y lo buscamos juntos.",
)
DESPEDIDAS = (
    "Gracias por pasar por Dismac! Cualquier cosa, aca estoy.",
    "Chau! Cuando quieras seguimos, te espero.",
)
AGRADECIMIENTOS = (
    "Un gusto! Si necesitas algo mas, me decis.",
    "De nada! Seguimos cuando quieras.",
)


class ClasificadorIntencion:
    """SRP: clasificar el mensaje del cliente y, si es una intencion trivial,
    devolver una respuesta directa para saltarse el loop tool-calling.

    Clasifica por regex/keywords — rapido, barato, sin LLM.
    """

    MAX_LEN_SHORTCIRCUIT = 60

    def clasificar(self, mensaje: str) -> Intencion:
        texto = (mensaje or "").strip()
        if not texto:
            return Intencion.OTRO
        if len(texto) <= self.MAX_LEN_SHORTCIRCUIT:
            if RX_SALUDO.match(texto):
                return Intencion.SALUDO
            if RX_DESPEDIDA.match(texto):
                return Intencion.DESPEDIDA
            if RX_GRACIAS.match(texto):
                return Intencion.GRACIAS
        if RX_CARRITO.search(texto):
            return Intencion.ACCION_CARRITO
        if RX_PRODUCTO.search(texto):
            return Intencion.CONSULTA_PRODUCTO
        return Intencion.OTRO

    def respuesta_directa(self, mensaje: str) -> RespuestaIntencionDirecta | None:
        intencion = self.clasificar(mensaje)
        if intencion == Intencion.SALUDO:
            return RespuestaIntencionDirecta(intencion, random.choice(SALUDOS))
        if intencion == Intencion.DESPEDIDA:
            return RespuestaIntencionDirecta(intencion, random.choice(DESPEDIDAS))
        if intencion == Intencion.GRACIAS:
            return RespuestaIntencionDirecta(intencion, random.choice(AGRADECIMIENTOS))
        return None
