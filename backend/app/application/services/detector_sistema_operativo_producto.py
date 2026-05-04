from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class AdvertenciaSO:
    so_detectado: str
    advertencia: str
    bloquea_uso_profesional: bool


class DetectorSistemaOperativoProducto:
    """SRP: identificar SO declarado en el producto y emitir advertencia.

    FreeDOS y ChromeOS son dos casos comunes que el cliente confunde con
    'Windows preinstalado'. El sistema debe avisar antes de la compra."""

    _RX_FREEDOS = re.compile(r"\b(freedos|free\s*dos|sin\s*sistema|no\s*os)\b", re.IGNORECASE)
    _RX_CHROMEOS = re.compile(r"\b(chrome\s*os|chromebook)\b", re.IGNORECASE)
    _RX_WINDOWS = re.compile(r"\b(win11|win10|windows\s*1[01])\b", re.IGNORECASE)
    _RX_LINUX = re.compile(r"\b(linux|ubuntu|fedora|debian)\b", re.IGNORECASE)
    _RX_MACOS = re.compile(r"\b(macos|mac\s*os|osx)\b", re.IGNORECASE)

    @classmethod
    def detectar(cls, producto) -> AdvertenciaSO | None:
        nombre = (getattr(producto, "nombre", "") or "")
        so_field = (getattr(producto, "sistema_operativo", "") or "")
        texto = f"{nombre} {so_field}"

        if cls._RX_FREEDOS.search(texto):
            return AdvertenciaSO(
                so_detectado="FreeDOS",
                advertencia=(
                    "Viene con FreeDOS — necesitaras instalar Windows o Linux antes de "
                    "usarla con software comun (AutoCAD, Office, etc.)."
                ),
                bloquea_uso_profesional=False,
            )
        if cls._RX_CHROMEOS.search(texto):
            return AdvertenciaSO(
                so_detectado="ChromeOS",
                advertencia=(
                    "Es Chromebook (ChromeOS) — no corre Windows. No sirve para AutoCAD, "
                    "Civil 3D, SolidWorks ni la mayoria del software de ingenieria/diseno."
                ),
                bloquea_uso_profesional=True,
            )
        return None
