from __future__ import annotations

import re


class DetectorUpgradeIntent:

    _PATRONES_UPGRADE = [
        r"quiero\s+cambiar\s+mi\s+\w",
        r"quiero\s+cambiarme\s+de",
        r"me\s+quiero\s+cambiar",
        r"tengo\s+uno\s+viejo",
        r"el\s+m[ií]o\s+ya\s+est[aá]\s+viejo",
        r"se\s+me\s+arruinó",
        r"se\s+me\s+rompi[oó]",
        r"se\s+me\s+dañó",
        r"se\s+me\s+da[nñ][oó]",
        r"ya\s+no\s+sirve",
        r"ya\s+no\s+jala",
        r"ya\s+no\s+da",
        r"ya\s+no\s+funciona",
        r"quiero\s+mejorar\s+mi\s+\w",
        r"quiero\s+actualizarme",
        r"quiero\s+algo\s+mejor",
        r"quiero\s+uno\s+mejor",
        r"tiene\s+\d+\s+años",
        r"lleva\s+\d+\s+años",
        r"ya\s+tiene\s+\d+\s+años",
        r"\bupgrade\s+de\b",
        r"actualizar\s+mi\s+\w",
        r"me\s+qued[eé]\s+sin\s+\w",
        r"se\s+me\s+muri[oó]\s+(el|la)\s+\w",
        r"quiero\s+renovar\s+mi\s+\w",
        r"tengo\s+\w+\s+y\s+quiero\s+(uno|algo)\s+mejor",
        r"tengo\s+\w+\s+pero\s+quiero\s+(algo|uno)\s+mejor",
    ]

    _COMPILED_UPGRADE = [re.compile(p, re.IGNORECASE) for p in _PATRONES_UPGRADE]

    _MARCAS = [
        "samsung", "apple", "lg", "hp", "lenovo", "asus", "acer", "sony",
        "xiaomi", "motorola", "huawei", "dell", "toshiba", "panasonic",
        "hisense", "tcl", "philips", "nokia", "oppo", "vivo", "realme",
    ]

    _CATEGORIAS = [
        "celular", "laptop", "tele", "televisor", "lavadora", "tablet",
        "computadora", "computador", "pc", "notebook", "monitor", "impresora",
        "nevera", "refrigerador", "microondas", "licuadora", "plancha",
        "smartphone", "tel[eé]fono",
    ]

    _PRODUCTO_TOKENS = "|".join(_MARCAS + _CATEGORIAS)
    _RE_PRODUCTO = re.compile(
        r"mi\s+(" + _PRODUCTO_TOKENS + r")",
        re.IGNORECASE,
    )

    @classmethod
    def es_upgrade(cls, mensaje: str) -> bool:
        for patron in cls._COMPILED_UPGRADE:
            if patron.search(mensaje):
                return True
        return False

    @classmethod
    def producto_actual(cls, mensaje: str) -> str | None:
        match = cls._RE_PRODUCTO.search(mensaje)
        if match:
            return match.group(1).lower()
        return None
