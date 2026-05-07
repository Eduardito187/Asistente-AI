from __future__ import annotations

from difflib import SequenceMatcher
from typing import Iterable, Optional

from ...domain.shared.normalizador_fonetico import NormalizadorFonetico


class MatcherFuzzyKeywords:
    """SRP: dado una palabra y un diccionario, devuelve la entrada del
    diccionario mas cercana segun ratio fonetico/textual. Sirve para
    tolerar typos en deteccion de keywords ('chrombuk' -> 'chromebook',
    'qiero' -> 'quiero').

    Estrategia: combina SequenceMatcher (ratio textual) con
    NormalizadorFonetico (colapsa equivalencias del español como h muda,
    b<->v, c suave, etc.) y se queda con el ratio mas alto. El minimo
    por defecto (0.78) es coherente con `ResolvedorCategoriaCercana`."""

    _RATIO_MIN_DEFAULT = 0.78

    @classmethod
    def mejor_match(
        cls,
        palabra: str,
        diccionario: Iterable[str],
        *,
        ratio_min: float = _RATIO_MIN_DEFAULT,
    ) -> Optional[str]:
        if not palabra:
            return None
        p = palabra.lower().strip()
        if not p:
            return None
        p_fon = NormalizadorFonetico.normalizar(p)
        mejor: tuple[float, str] | None = None
        for candidato in diccionario:
            c = candidato.lower()
            if c == p:
                return candidato
            # Filtro grueso por longitud: ratios bajan rapido cuando difieren
            # mas de 30%; saltamos para no pagar SequenceMatcher.
            if abs(len(c) - len(p)) > max(2, len(c) // 3):
                continue
            ratio_textual = SequenceMatcher(None, p, c).ratio()
            ratio_fonetico = SequenceMatcher(
                None, p_fon, NormalizadorFonetico.normalizar(c)
            ).ratio()
            ratio = max(ratio_textual, ratio_fonetico)
            if ratio < ratio_min:
                continue
            if mejor is None or ratio > mejor[0]:
                mejor = (ratio, candidato)
        return mejor[1] if mejor else None
