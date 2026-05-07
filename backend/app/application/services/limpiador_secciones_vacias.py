from __future__ import annotations

import re


class LimpiadorSeccionesVacias:
    """SRP: elimina secciones plantilla del LLM que quedaron sin contenido
    util. Implementa la regla 'no mostrar Recomendacion principal sin un
    producto valido' (feedback usuario 2026-05-07).

    El LLM aprendio el formato del system_prompt:

        **Recomendación principal:**
        - Por qué conviene: ...

        **Alternativas:**
        - Opción económica: ...

        **Conclusión:**
        - ...

    A veces produce uno de estos headers SIN un bullet con SKU debajo.
    Esa seccion confunde al cliente y rompe el formato. La eliminamos
    determinista en post-proceso: si entre dos headers no hay ninguna
    linea con [SKU-PATTERN], la seccion entera (header + body) se borra."""

    # Headers en negritas que el prompt define como secciones canonicas.
    _RX_HEADER_SECCION = re.compile(
        r"^\s*\*\*\s*"
        r"(?:Recomendaci[oó]n\s+principal|Alternativas?|Conclusi[oó]n|Resumen)"
        r"\s*:?\s*\*\*\s*$",
        re.IGNORECASE,
    )
    # Cualquier referencia a un SKU dentro de los corchetes — el indicador
    # de "esta seccion realmente cita un producto".
    _RX_SKU_CITADO = re.compile(r"\[[A-Z0-9][A-Z0-9_\-#./]{2,}\]")

    @classmethod
    def limpiar(cls, respuesta: str) -> str:
        if not respuesta or "**" not in respuesta:
            return respuesta
        lineas = respuesta.split("\n")
        bloques = cls._partir_en_bloques(lineas)
        salida: list[str] = []
        for bloque in bloques:
            if cls._es_seccion_vacia(bloque):
                continue
            salida.extend(bloque)
        return "\n".join(salida).strip()

    @classmethod
    def _partir_en_bloques(cls, lineas: list[str]) -> list[list[str]]:
        """Divide el texto en bloques delimitados por headers de seccion.
        Cada header inicia un bloque nuevo; el primer bloque (sin header)
        es el preambulo que NO se evalua como 'seccion vacia'."""
        bloques: list[list[str]] = [[]]
        for linea in lineas:
            if cls._RX_HEADER_SECCION.match(linea):
                bloques.append([linea])
            else:
                bloques[-1].append(linea)
        return bloques

    @classmethod
    def _es_seccion_vacia(cls, bloque: list[str]) -> bool:
        if not bloque:
            return False
        primera = bloque[0]
        if not cls._RX_HEADER_SECCION.match(primera):
            return False
        # El cuerpo debe contener algun [SKU]; si no, la seccion no aporta.
        cuerpo = "\n".join(bloque[1:])
        if cls._RX_SKU_CITADO.search(cuerpo):
            return False
        return True
