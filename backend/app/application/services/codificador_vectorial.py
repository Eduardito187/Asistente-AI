from __future__ import annotations

import struct


class CodificadorVectorial:
    """SRP: serializar/deserializar vectores float32 hacia/desde bytes (BLOB)."""

    @staticmethod
    def a_bytes(vector: list[float]) -> bytes:
        return struct.pack(f"<{len(vector)}f", *vector)

    @staticmethod
    def desde_bytes(blob: bytes) -> list[float]:
        if not blob:
            return []
        count = len(blob) // 4
        return list(struct.unpack(f"<{count}f", blob))
