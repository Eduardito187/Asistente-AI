from __future__ import annotations

import re


class DetectorClienteMayorista:

    _PATRON = re.compile(
        r"\bal\s+por\s+mayor\b"
        r"|\bpor\s+mayor\b"
        r"|\bmayoreo\b"
        r"|\bmayorista\b"
        r"|para\s+distribuir"
        r"|para\s+revender"
        r"|para\s+mi\s+tienda"
        r"|para\s+mi\s+negocio\s+de"
        r"|quiero\s+\d+\s+unidades"
        r"|necesito\s+\d+\s+unidades"
        r"|varias\s+unidades"
        r"|m[uú]ltiples\s+unidades"
        r"|precio\s+especial\s+por\s+cantidad"
        r"|descuento\s+por\s+volumen"
        r"|precio\s+de\s+distribuidor"
        r"|para\s+mis\s+empleados"
        r"|para\s+la\s+empresa"
        r"|\blote\s+de\b"
        r"|pedido\s+grande"
        r"|al\s+por\s+junto",
        re.IGNORECASE,
    )

    _PATRON_CANTIDAD = re.compile(
        r"(?:quiero|necesito)\s+(\d+)\s+unidades",
        re.IGNORECASE,
    )

    @classmethod
    def es_mayorista(cls, mensaje: str) -> bool:
        return bool(cls._PATRON.search(mensaje))

    @classmethod
    def cantidad_aproximada(cls, mensaje: str) -> int | None:
        m = cls._PATRON_CANTIDAD.search(mensaje)
        if m:
            n = int(m.group(1))
            return n if n >= 2 else None
        return None
