from __future__ import annotations

import re

from .formato_solicitado import FormatoSolicitado


class AjustadorRespuestaFormato:
    """SRP: enforce los caps duros del FormatoSolicitado sobre la respuesta
    final del LLM. El LLM hace su mejor esfuerzo via la directiva inyectada
    al prompt; este ajustador es el guard determinista por si el modelo se
    pasa.

    Operaciones (en orden):
    1. Cap por `max_productos`: deja solo las primeras N lineas con `[SKU]`.
    2. Cap por `max_frases` GLOBAL: trunca al N-esimo punto/signo final.
    3. Recorte de cierres-pregunta-redundante ya lo hace
       `SilenciadorPreguntasRedundantes` y `RecortadorCierresComerciales`,
       no duplicar."""

    _RX_LINEA_CON_SKU = re.compile(r"\[[A-Z0-9][A-Z0-9_\-#./]{2,}\]")
    _RX_FIN_FRASE = re.compile(r"[\.!\?]")

    @classmethod
    def ajustar(cls, respuesta: str, fmt: FormatoSolicitado) -> str:
        if not respuesta or fmt.vacio():
            return respuesta
        texto = respuesta
        if fmt.max_productos is not None:
            texto = cls._cap_productos(texto, fmt.max_productos)
        # max_frases globales solo cuando NO hay estructura — si el cliente
        # pidio 'comprar/evitar/por que' la estructura ya define las lineas
        # y el cap global cortaria el formato pedido.
        if fmt.forma is None and fmt.max_frases is not None and fmt.max_frases >= 1:
            texto = cls._cap_frases_globales(texto, fmt.max_frases)
        return texto.strip()

    @classmethod
    def _cap_productos(cls, texto: str, maximo: int) -> str:
        """Mantiene las primeras `maximo` lineas que contienen un [SKU];
        las lineas sin SKU se preservan (encabezados, conclusiones, razones).
        Si el texto tiene <= maximo lineas con SKU, no toca nada."""
        lineas = texto.split("\n")
        contador_sku = 0
        salida: list[str] = []
        for linea in lineas:
            if cls._RX_LINEA_CON_SKU.search(linea):
                contador_sku += 1
                if contador_sku > maximo:
                    continue
            salida.append(linea)
        return "\n".join(salida)

    @classmethod
    def _cap_frases_globales(cls, texto: str, maximo: int) -> str:
        """Cuenta oraciones globalmente en TODO el texto y trunca al cierre
        de la N-esima. Reglas:

        - Linea con `[SKU]`: cuenta 1 oracion (los puntos internos del nombre
          no inflan el conteo).
        - Linea sin SKU SIN `.`/`!`/`?`: encabezado/separador, NO cuenta como
          oracion (no consume cap).
        - Linea sin SKU CON N puntos: cuenta N oraciones."""
        if maximo < 1:
            return texto
        lineas = texto.split("\n")
        salida: list[str] = []
        consumidas = 0
        for linea in lineas:
            if consumidas >= maximo:
                break
            limpia = linea.rstrip()
            if not limpia.strip():
                salida.append(linea)
                continue
            tiene_sku = bool(cls._RX_LINEA_CON_SKU.search(limpia))
            if tiene_sku:
                salida.append(limpia)
                consumidas += 1
                continue
            posiciones = [m.end() for m in cls._RX_FIN_FRASE.finditer(limpia)]
            if not posiciones:
                # Encabezado/separador sin punto: pasa sin consumir cap.
                salida.append(limpia)
                continue
            cabe = maximo - consumidas
            if len(posiciones) <= cabe:
                salida.append(limpia)
                consumidas += len(posiciones)
                continue
            corte = posiciones[cabe - 1]
            salida.append(limpia[:corte].rstrip())
            consumidas = maximo
        return "\n".join(salida).strip()
