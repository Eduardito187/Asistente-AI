"""Evaluador offline de conversaciones doradas.

Uso:
    python scripts/evaluar_conversaciones.py [--url http://localhost:8000] [--dataset scripts/conversaciones_doradas.json]

El script abre una sesion por caso, envia los mensajes al backend y valida
asertos declarativos (texto que debe/no debe aparecer, tools requeridas/prohibidas).
Sale con codigo 0 si todo paso, 1 si hubo fallas.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from evaluador_offline import ReporteConsola, RunnerCaso


def main() -> int:
    args = _parse_args()
    casos: list[dict] = []
    for ds in args.dataset:
        casos.extend(_cargar_dataset(ds))
    runner = RunnerCaso(base_url=args.url)
    resultados = [runner.correr(c) for c in casos]
    return ReporteConsola.imprimir(resultados)


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://localhost:8000")
    parser.add_argument(
        "--dataset",
        action="append",
        default=None,
        help="Ruta a un JSON de casos. Se puede repetir.",
    )
    args = parser.parse_args()
    if not args.dataset:
        args.dataset = [str(Path(__file__).parent / "conversaciones_doradas.json")]
    return args


def _cargar_dataset(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


if __name__ == "__main__":
    sys.exit(main())
