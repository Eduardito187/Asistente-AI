from __future__ import annotations

import re

from ...domain.shared.vocabulario_controlado.glosario_palabras_controladas import (
    GlosarioPalabrasControladas,
)


class FiltroVocabularioControlado:
    """Post-procesador de salida: sustituye palabras prohibidas por sus
    equivalentes aprobados según GlosarioPalabrasControladas.

    El patrón regex se compila una sola vez (lazy, a nivel de clase).
    Para añadir una nueva palabra prohibida solo hay que editar el Glosario.
    """

    _patron: re.Pattern | None = None
    _mapa: dict[str, str] = {}

    @classmethod
    def _asegurar_compilado(cls) -> None:
        if cls._patron is not None:
            return
        mapa: dict[str, str] = {}
        for regla in GlosarioPalabrasControladas.reglas():
            for prohibida, aprobada in regla.mapa:
                mapa[prohibida.lower()] = aprobada
        if not mapa:
            cls._patron = re.compile(r"(?!x)x")  # nunca hace match
            cls._mapa = {}
            return
        # Ordenar de mayor a menor longitud para que "descuentazo" tenga
        # prioridad sobre "descuento" en el match.
        alternacion = "|".join(re.escape(k) for k in sorted(mapa, key=len, reverse=True))
        cls._patron = re.compile(r"\b(" + alternacion + r")\b", re.IGNORECASE)
        cls._mapa = mapa

    @classmethod
    def aplicar(cls, texto: str) -> str:
        if not texto:
            return texto
        cls._asegurar_compilado()

        def _sustituir(m: re.Match) -> str:
            return cls._mapa.get(m.group(0).lower(), m.group(0))

        return cls._patron.sub(_sustituir, texto)
