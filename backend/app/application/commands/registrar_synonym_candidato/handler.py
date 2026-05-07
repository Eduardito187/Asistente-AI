from __future__ import annotations

import logging
from typing import Callable

from ...ports import UnitOfWork
from .command import RegistrarSynonymCandidatoCommand

log = logging.getLogger("registrar_synonym_candidato")


class RegistrarSynonymCandidatoHandler:
    """Handler CQRS: upsert sobre synonyms_candidatos. Devuelve el contador
    actualizado para que el caller pueda actuar (alerta sobre threshold)."""

    def __init__(self, uow_factory: Callable[[], UnitOfWork]) -> None:
        self._uow_factory = uow_factory

    def ejecutar(self, cmd: RegistrarSynonymCandidatoCommand) -> int:
        try:
            with self._uow_factory() as uow:
                count = uow.synonyms_candidatos.upsert_incrementando(
                    cmd.termino, cmd.categoria_inferida
                )
                uow.commit()
                return count
        except Exception as exc:
            log.warning("no se pudo registrar synonym candidato: %s", exc)
            return 0
