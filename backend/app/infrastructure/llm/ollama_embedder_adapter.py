from __future__ import annotations

import logging

import httpx

from ...application.ports.embedder_port import EmbedderPort

log = logging.getLogger("ollama_embedder")


class OllamaEmbedderAdapter(EmbedderPort):
    """Adapter sobre /api/embed de Ollama. SRP: producir embeddings."""

    def __init__(self, host: str, model: str, timeout: float = 120.0) -> None:
        self._host = host
        self._model = model
        self._timeout = timeout

    @property
    def modelo(self) -> str:
        return self._model

    def embed(self, textos: list[str]) -> list[list[float]]:
        if not textos:
            return []
        payload = {"model": self._model, "input": textos}
        try:
            with httpx.Client(timeout=self._timeout) as client:
                r = client.post(f"{self._host}/api/embed", json=payload)
                r.raise_for_status()
                data = r.json()
            return list(data.get("embeddings") or [])
        except Exception as exc:
            log.warning("ollama embed fallo (%s items): %s", len(textos), exc)
            return []
