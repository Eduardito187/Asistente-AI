from __future__ import annotations

import re
from dataclasses import dataclass

from ...domain.shared.normalizacion import NormalizadorTexto


@dataclass(frozen=True)
class ComparacionExplicita:
    """Resultado: el cliente mencionó 2+ productos que quiere comparar.
    Los fragmentos son tal cual el usuario los escribió (sin normalizar) para
    que el resolver los mapee a SKUs específicos."""

    fragmentos: list[str]


class DetectorComparacionExplicita:
    """SRP: detecta cuando el cliente compara 2+ modelos nombrándolos
    explícitamente ('X vs Y', 'X o Y', 'entre X y Y', 'comparame X con Y',
    'cual es mejor X o Y') y extrae los fragmentos para que el resolver
    los mapee a SKUs. No interpreta: solo separa."""

    # Conectores que el usuario suele usar para listar dos modelos.
    _SEPARADORES = re.compile(
        r"\s+(?:vs|versus|\/|\\|contra|frente\s+a|y|o|u|versus)\s+",
        re.IGNORECASE,
    )

    # Disparadores de intención de comparación.
    _RX_DISPARADORES = re.compile(
        r"\b(?:"
        r"compar(?:a|ame|alos|alas|amelos)\s+(?:el|la|los|las)?"
        r"|diferenc(?:ia|ias)\s+entre"
        r"|entre\s+(?:el|la|los|las)?"
        r"|cual\s+(?:es\s+)?(?:el\s+)?mejor\s+(?:entre|el|la)?"
        r"|estoy\s+(?:entre|dudando\s+entre)"
        r"|dudas?\s+entre"
        r"|(?:quiero|queres)\s+comparar"
        r"|que\s+(?:me\s+)?conviene\s+(?:mas\s+)?entre"
        r")\b",
        re.IGNORECASE,
    )

    # Patrón "A vs B" sin disparador previo (atajo popular).
    _RX_VS_DIRECTO = re.compile(
        r"\S+\s+(?:vs|versus)\s+\S+",
        re.IGNORECASE,
    )

    _MIN_LONGITUD_FRAGMENTO = 3
    _MIN_FRAGMENTOS = 2
    _MAX_FRAGMENTOS = 4

    @classmethod
    def detectar(cls, texto: str) -> ComparacionExplicita | None:
        if not texto:
            return None
        disparador = cls._RX_DISPARADORES.search(texto)
        vs_directo = cls._RX_VS_DIRECTO.search(texto)
        if not disparador and not vs_directo:
            return None

        resto = texto[disparador.end():] if disparador else texto
        fragmentos = cls._dividir(resto)
        if len(fragmentos) < cls._MIN_FRAGMENTOS:
            return None
        return ComparacionExplicita(fragmentos=fragmentos[: cls._MAX_FRAGMENTOS])

    @classmethod
    def _dividir(cls, resto: str) -> list[str]:
        """Divide por separadores (vs / y / o / contra) y limpia cada
        fragmento. Filtra los muy cortos para evitar falsos positivos
        ('un', 'el', 'o')."""
        partes = cls._SEPARADORES.split(resto)
        limpios: list[str] = []
        for p in partes:
            frag = cls._limpiar(p)
            if len(NormalizadorTexto.normalizar(frag).split()) >= 1 and len(frag) >= cls._MIN_LONGITUD_FRAGMENTO:
                limpios.append(frag)
        return limpios

    @staticmethod
    def _limpiar(frag: str) -> str:
        frag = frag.strip(" ,.;:?!¿¡\"'")
        # quitar artículos y prefijos comunes al inicio para que el resolver
        # resuelva mejor ('el s26 ultra' -> 's26 ultra')
        frag = re.sub(r"^(?:el|la|los|las|un|una|unos|unas|ese|esa)\s+", "", frag, flags=re.IGNORECASE)
        return frag.strip()
