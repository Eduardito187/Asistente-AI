from dataclasses import dataclass


@dataclass(frozen=True)
class ResultadoCatalogoAkeneo:
    insertados: int
    omitidos: int
