from __future__ import annotations

import json
import logging
import re
from typing import Any

from ..ports.llm_port import LLMPort
from .resultado_validacion_producto import ResultadoValidacionProducto

log = logging.getLogger("validador_producto_real")

PROMPT = (
    "Sos un validador de productos de retail de electrónica, electrodomésticos, "
    "tecnología y hogar. Recibís un texto libre del cliente y debés decidir si "
    "corresponde a un PRODUCTO REAL comercial (aunque Dismac no lo tenga en "
    "catálogo).\n\n"
    "Responde ÚNICAMENTE con un objeto JSON válido, sin texto adicional, sin "
    "markdown, sin explicaciones. Estructura exacta:\n"
    "{\n"
    '  "es_real": boolean,\n'
    '  "nombre_canonico": string|null,\n'
    '  "categoria": string|null,\n'
    '  "marca": string|null\n'
    "}\n\n"
    "Reglas:\n"
    "- `es_real=true` SOLO si es un producto comercial reconocible (marca/modelo "
    "o categoría concreta, p.ej. 'iPhone 15 Pro Max', 'televisor OLED 55\"', "
    "'freidora de aire Oster 5L').\n"
    "- `es_real=false` para galimatías, frases sin sentido, categorías "
    "demasiado genéricas ('algo bueno'), o cosas que no sean productos retail.\n"
    "- `nombre_canonico`: el nombre más claro y breve del producto, o null.\n"
    "- `categoria`: una de ['Laptops', 'Celulares', 'Televisores', "
    "'Electrodomésticos', 'Audio', 'Computación', 'Hogar', 'Videojuegos', "
    "'Otro'] o null.\n"
    "- `marca`: solo la marca del fabricante si es clara; null si no aplica.\n"
)


class ValidadorProductoReal:
    """SRP: consultar al LLM si un texto de cliente refiere un producto real."""

    def __init__(self, llm: LLMPort) -> None:
        self._llm = llm

    async def validar(self, texto_cliente: str) -> ResultadoValidacionProducto:
        texto = (texto_cliente or "").strip()
        if not texto:
            return ResultadoValidacionProducto(False, None, None, None)
        try:
            msg = await self._llm.chat(
                [
                    {"role": "system", "content": PROMPT},
                    {"role": "user", "content": texto},
                ],
                [],
            )
            data = self._parse_json(msg.content or "")
            return ResultadoValidacionProducto(
                es_real=bool(data.get("es_real")),
                nombre_canonico=self._str_o_none(data.get("nombre_canonico")),
                categoria=self._str_o_none(data.get("categoria")),
                marca=self._str_o_none(data.get("marca")),
            )
        except Exception as exc:
            log.warning("validador producto real fallo: %s", exc)
            return ResultadoValidacionProducto(False, None, None, None)

    @staticmethod
    def _parse_json(texto: str) -> dict[str, Any]:
        limpio = texto.strip()
        fence = re.search(r"\{.*\}", limpio, re.DOTALL)
        if fence:
            limpio = fence.group(0)
        return json.loads(limpio)

    @staticmethod
    def _str_o_none(valor: Any) -> str | None:
        if valor is None:
            return None
        s = str(valor).strip()
        return s or None
