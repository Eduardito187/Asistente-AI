from __future__ import annotations

import re


class LimpiadorEmojiSpam:
    """Limita emojis en la respuesta a un maximo de N (default 2).
    Preserva los primeros N emojis encontrados, stripea el resto."""

    _MAX_EMOJIS = 2

    # Rango Unicode que cubre los emojis mas comunes sin depender del
    # paquete 'emoji'. Incluye Emoticons, Misc Symbols, Dingbats,
    # Supplemental Symbols, Transport & Map, etc.
    _EMOJI_RX = re.compile(
        r"[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0000FE00-\U0000FEFF]"
    )

    @classmethod
    def limpiar(cls, texto: str, max_emojis: int = _MAX_EMOJIS) -> str:
        if not texto:
            return texto
        if not cls._tiene_emojis(texto):
            return texto
        return cls._recortar(texto, max_emojis)

    @staticmethod
    def _tiene_emojis(texto: str) -> bool:
        return bool(LimpiadorEmojiSpam._EMOJI_RX.search(texto))

    @classmethod
    def _recortar(cls, texto: str, max_emojis: int) -> str:
        contador = 0

        def _reemplazar(m: re.Match) -> str:
            nonlocal contador
            contador += 1
            if contador <= max_emojis:
                return m.group(0)
            return ""

        return cls._EMOJI_RX.sub(_reemplazar, texto)
