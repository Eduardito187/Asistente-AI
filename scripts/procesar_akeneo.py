#!/usr/bin/env python3
"""
scripts/procesar_akeneo.py
--------------------------
Limpia y prepara data/akeneo.csv para la ingesta.

Operaciones por cada celda (cabeceras incluidas):
  1. Elimina etiquetas HTML (<p>, <br>, <strong>, etc.)
  2. Decodifica entidades HTML (&nbsp; → espacio, &amp; → &, etc.)
  3. Elimina escapes de Excel como _x000D_ (CR) y _x000A_ (LF)
  4. Elimina corchetes [ ] y llaves { }
  5. Elimina comillas: simples ' dobles " graves ` tipográficas " " ' ' « »
  6. Elimina el sufijo " (español Bolivia)" en cabeceras y valores
  7. Normaliza espacios múltiples y recorta extremos

Filtros de filas:
  - Se excluyen productos cuyo campo Clacom sea:
      Cat. M - Mayorista | Cat. R - Repuesto | Cat. O - Obsoletos

Columnas completamente vacías (ningún producto tiene valor) se eliminan.

Salida: data/process/akeneo_processed.csv — UTF-8, separador ;
"""
from __future__ import annotations

import csv
import html as html_module
import pathlib
import re
import sys
import time

# ---------------------------------------------------------------------------
# Rutas
# ---------------------------------------------------------------------------
_ROOT = pathlib.Path(__file__).resolve().parent.parent
_INPUT = _ROOT / "data" / "akeneo.csv"
_OUTPUT_DIR = _ROOT / "data" / "process"
_OUTPUT = _OUTPUT_DIR / "akeneo_processed.csv"

# ---------------------------------------------------------------------------
# Patrones de limpieza
# ---------------------------------------------------------------------------
_RX_TAG = re.compile(r"<[^>]+>", re.DOTALL)
_RX_EXCEL_ESC = re.compile(r"_x[0-9A-Fa-f]{4}_")  # _x000D_ _x000A_ etc.
_RX_SPACES = re.compile(r"[ \t\xa0]{2,}")
_RX_LOCALE_TAG = re.compile(r" \(español Bolivia\)", re.IGNORECASE)

_CHARS_A_BORRAR = (
    "\"'`"
    "“”"   # " "
    "‘’"   # ' '
    "«»"   # « »
    "[]{}"
)
_TRANS_BORRAR = str.maketrans("", "", _CHARS_A_BORRAR)

# Valores de Clacom que se excluyen del catálogo procesado (comparación lowercase)
_CLACOM_EXCLUIDOS = {
    "cat. m - mayorista",
    "cat. r - repuesto",
    "cat. o - obsoletos",
}


# ---------------------------------------------------------------------------
# Limpieza de celdas
# ---------------------------------------------------------------------------
def limpiar(valor: str) -> str:
    """Limpia una celda: HTML → entidades → escapes Excel → chars especiales → espacios."""
    if not valor:
        return ""
    v = _RX_TAG.sub(" ", valor)
    v = html_module.unescape(v)
    v = v.replace("\xa0", " ").replace("\r", " ").replace("\n", " ")
    v = _RX_EXCEL_ESC.sub("", v)
    v = v.translate(_TRANS_BORRAR)
    v = _RX_LOCALE_TAG.sub("", v)
    v = _RX_SPACES.sub(" ", v)
    return v.strip()


# ---------------------------------------------------------------------------
# Helpers de I/O
# ---------------------------------------------------------------------------
def _iter_filas(path: pathlib.Path):
    with open(path, encoding="utf-8", errors="replace", newline="") as fh:
        yield from csv.reader(fh, delimiter=";")


def _detectar_clacom(cabeceras_raw: list[str]) -> int | None:
    idx = next((j for j, h in enumerate(cabeceras_raw) if "lacom" in h.lower()), None)
    if idx is None:
        print("AVISO: columna Clacom no encontrada — no se aplicará filtro de exclusión.")
    else:
        print(f"Filtro Clacom       : columna {idx} — excluyendo {sorted(_CLACOM_EXCLUIDOS)}")
    return idx


def _fila_excluida(fila: list[str], clacom_idx: int | None) -> bool:
    if clacom_idx is None:
        return False
    val = fila[clacom_idx].strip().lower() if clacom_idx < len(fila) else ""
    return val in _CLACOM_EXCLUIDOS


def _normalizar(fila: list[str], n_cols: int) -> list[str]:
    if len(fila) < n_cols:
        fila.extend([""] * (n_cols - len(fila)))
    return fila


# ---------------------------------------------------------------------------
# Paso 1: escanear columnas con contenido (respetando filtro Clacom)
# ---------------------------------------------------------------------------
def _escanear_columnas(
    n_cols: int, clacom_idx: int | None
) -> tuple[list[int], int, int]:
    """Devuelve (indices_activos, filas_incluidas, filas_excluidas)."""
    tiene_contenido = [False] * n_cols
    incluidas = excluidas = 0

    for i, fila in enumerate(_iter_filas(_INPUT)):
        if i == 0:
            continue  # cabecera
        _normalizar(fila, n_cols)
        if _fila_excluida(fila, clacom_idx):
            excluidas += 1
            continue
        incluidas += 1
        for j in range(n_cols):
            if not tiene_contenido[j] and limpiar(fila[j]):
                tiene_contenido[j] = True
        if incluidas % 20_000 == 0:
            print(f"  {incluidas:>8,} filas procesadas…")

    return [j for j in range(n_cols) if tiene_contenido[j]], incluidas, excluidas


# ---------------------------------------------------------------------------
# Paso 2: escribir CSV limpio
# ---------------------------------------------------------------------------
def _escribir_csv(
    cabeceras: list[str],
    indices_activos: list[int],
    n_cols: int,
    clacom_idx: int | None,
) -> int:
    """Escribe el CSV de salida y devuelve el número de filas escritas."""
    _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    escritas = 0
    with open(_OUTPUT, "w", encoding="utf-8", newline="") as fh_out:
        writer = csv.writer(fh_out, delimiter=";", quoting=csv.QUOTE_MINIMAL)
        writer.writerow([cabeceras[j] for j in indices_activos])
        for i, fila in enumerate(_iter_filas(_INPUT)):
            if i == 0:
                continue  # cabecera
            _normalizar(fila, n_cols)
            if _fila_excluida(fila, clacom_idx):
                continue
            writer.writerow([limpiar(fila[j]) for j in indices_activos])
            escritas += 1
            if escritas % 20_000 == 0:
                print(f"  {escritas:>8,} filas escritas…")
    return escritas


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    if not _INPUT.exists():
        print(f"ERROR: no se encontró {_INPUT}", file=sys.stderr)
        sys.exit(1)

    t0 = time.time()
    print(f"Entrada : {_INPUT}")
    print(f"Salida  : {_OUTPUT}\n")

    it = _iter_filas(_INPUT)
    cabeceras_raw = next(it)
    n_cols = len(cabeceras_raw)
    cabeceras = [limpiar(h) for h in cabeceras_raw]
    print(f"Columnas detectadas : {n_cols}")

    clacom_idx = _detectar_clacom(cabeceras_raw)

    print("Paso 1/2 — escaneando columnas con contenido...")
    indices_activos, n_incluidas, n_excluidas = _escanear_columnas(n_cols, clacom_idx)
    cols_eliminadas = n_cols - len(indices_activos)

    print(f"\nResultado del escaneo:")
    print(f"  Filas incluidas     : {n_incluidas:,}")
    print(f"  Filas excluidas     : {n_excluidas:,}  (Clacom: mayorista/repuesto/obsoleto)")
    print(f"  Columnas con datos  : {len(indices_activos)}")
    print(f"  Columnas eliminadas : {cols_eliminadas}  (completamente vacías)")

    print(f"\nPaso 2/2 — escribiendo CSV limpio...")
    escritas = _escribir_csv(cabeceras, indices_activos, n_cols, clacom_idx)

    elapsed = time.time() - t0
    size_mb = _OUTPUT.stat().st_size / 1_048_576
    separador = "=" * 60
    print(f"\n{separador}")
    print(f"COMPLETADO en {elapsed:.1f}s")
    print(f"Archivo : {_OUTPUT}")
    print(f"Tamaño  : {size_mb:.1f} MB")
    print(f"Filas   : {escritas:,}")
    print(f"Columnas: {len(indices_activos)} (de {n_cols} originales, -{cols_eliminadas} vacías)")
    print(separador)


if __name__ == "__main__":
    main()
