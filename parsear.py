#!/usr/bin/env python3
"""Recorre el vault y genera la capa derivada.

    python parsear.py <ruta-del-diario>
    python parsear.py <ruta> --destino derivado/
    python parsear.py <ruta> --resumen        sin escribir nada

La capa derivada se regenera entera cada vez. Es desechable por diseño: el dato
vive en los `.md` (D1).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parser.exportar import exportar  # noqa: E402
from parser.lector import leer_vault  # noqa: E402
from parser.tidy import tabla_dias, tabla_ingestas  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Genera la capa derivada del registro.")
    cli.add_argument("ruta", type=Path, help="carpeta del diario (o un .md suelto)")
    cli.add_argument("--destino", type=Path, default=Path("derivado"),
                     help="dónde escribir parquet y SQLite (por defecto: derivado/)")
    cli.add_argument("--resumen", action="store_true", help="no escribe nada, sólo informa")
    args = cli.parse_args(argv)

    if not args.ruta.exists():
        print(f"no existe: {args.ruta}", file=sys.stderr)
        return 2

    dias = leer_vault(args.ruta)
    if not dias:
        print(f"no se encontró ninguna nota YYYY-MM-DD.md en {args.ruta}")
        return 1

    marco_dias = tabla_dias(dias)
    marco_ingestas = tabla_ingestas(dias)

    registrados = int(marco_dias["registrado"].sum())
    con_ingestas = int((marco_dias["n_ingestas"] > 0).sum())
    print(f"{len(marco_dias)} nota(s) · {registrados} día(s) registrado(s) · "
          f"{con_ingestas} con ingestas · {len(marco_ingestas)} ingesta(s)")
    print(f"del {marco_dias['fecha'].min()} al {marco_dias['fecha'].max()}")

    if args.resumen:
        return 0

    salidas = exportar(marco_dias, marco_ingestas, args.destino)
    for nombre, ruta in salidas.items():
        print(f"  → {ruta}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
