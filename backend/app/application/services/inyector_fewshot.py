from __future__ import annotations

from typing import Callable

from ..ports import UnitOfWork
from ..queries.obtener_ejemplos_fewshot import (
    ObtenerEjemplosFewShotHandler,
    ObtenerEjemplosFewShotQuery,
)


class InyectorFewShot:
    """SRP: construye bloque de ejemplos few-shot. Selecciona POR SIMILITUD
    de categoria/uso (#7 del review) para no inyectar 'laptop mama' cuando
    el cliente pide 'laptop ingenieria GPU dedicada'.

    Prioridad de inyeccion:
      1) GoldenConversations de la misma categoria (siempre primero)
      2) ConversacionCurada de la misma categoria
      3) Fallback: top conversaciones curadas globales

    Limita a max 3 ejemplos para no saturar el prompt."""

    LIMITE_DEFAULT = 3

    def __init__(
        self,
        ejemplos: ObtenerEjemplosFewShotHandler,
        uow_factory: Callable[[], UnitOfWork] | None = None,
    ) -> None:
        self._ejemplos = ejemplos
        self._uow_factory = uow_factory

    def bloque(self, limite: int | None = None) -> str:
        return self.bloque_para_contexto(None, None, limite=limite)

    def bloque_para_contexto(
        self,
        categoria: str | None,
        uso: str | None,
        limite: int | None = None,
    ) -> str:
        n = limite or self.LIMITE_DEFAULT
        ejemplos = self._recopilar(categoria, uso, n)
        if not ejemplos:
            return ""
        partes = [
            "EJEMPLOS DE CONVERSACIONES QUE FUNCIONARON BIEN "
            "(imita el tono calido, corto y resolutivo; NO copies SKUs ni precios):",
        ]
        for i, (cliente, asistente) in enumerate(ejemplos, 1):
            partes.append(
                f"\nEjemplo {i}:\nCliente: {self._recortar(cliente, 400)}\n"
                f"Dismi: {self._recortar(asistente, 600)}"
            )
        return "\n".join(partes)

    def _recopilar(
        self, categoria: str | None, uso: str | None, n: int
    ) -> list[tuple[str, str]]:
        out: list[tuple[str, str]] = []
        out.extend(self._goldens_para(categoria, uso))
        if len(out) < n:
            out.extend(self._curados_globales(n - len(out)))
        return out[:n]

    def _goldens_para(
        self, categoria: str | None, uso: str | None
    ) -> list[tuple[str, str]]:
        if not categoria or self._uow_factory is None:
            return []
        try:
            with self._uow_factory() as uow:
                goldens = uow.golden_conversations.buscar_por_categoria(
                    categoria=categoria, limite=4
                )
        except Exception:
            return []
        if uso:
            uso_low = uso.lower()
            goldens.sort(key=lambda g: 0 if (g.uso or "").lower() == uso_low else 1)
        return [(g.cliente_texto, g.asistente_texto) for g in goldens[:2]]

    def _curados_globales(self, n: int) -> list[tuple[str, str]]:
        try:
            conversaciones = self._ejemplos.ejecutar(
                ObtenerEjemplosFewShotQuery(limite=n)
            )
        except Exception:
            return []
        return [(c.cliente_texto, c.asistente_texto) for c in conversaciones]

    @staticmethod
    def _recortar(texto: str, n: int) -> str:
        t = (texto or "").strip().replace("\n", " ")
        return t if len(t) <= n else t[:n] + "..."
