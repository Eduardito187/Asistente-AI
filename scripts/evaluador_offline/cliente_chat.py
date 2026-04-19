from __future__ import annotations

import httpx


class ClienteChat:
    """SRP: hablar con el endpoint /chat y mantener el sesion_id del caso."""

    def __init__(self, base_url: str, timeout: float = 180.0) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._sesion_id: str | None = None

    @property
    def sesion_id(self) -> str | None:
        return self._sesion_id

    def enviar(self, mensaje: str) -> dict:
        payload: dict = {"mensaje": mensaje}
        if self._sesion_id:
            payload["sesion_id"] = self._sesion_id
        r = httpx.post(f"{self._base}/chat", json=payload, timeout=self._timeout)
        r.raise_for_status()
        data = r.json()
        self._sesion_id = data.get("sesion_id") or self._sesion_id
        return data
