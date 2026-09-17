#!/usr/bin/env python3
"""Genera el visor y lo abre en el navegador.

    python ver.py <ruta-del-diario>
    python ver.py <ruta> --salida derivado/visor.html
    python ver.py <ruta> --no-abrir

La página resultante es un único fichero HTML, local y autocontenido: no hace
ninguna petición de red. Son datos de estado emocional y pensamientos y la
superficie de exposición tiene que ser cero por defecto (D9).
"""

from __future__ import annotations

import argparse
import sys
import webbrowser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from parser.lector import leer_vault  # noqa: E402
from parser.tidy import tabla_dias, tabla_ingestas  # noqa: E402
from visor.generar import generar  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Genera el visor del registro y lo abre.")
    cli.add_argument("ruta", type=Path, help="carpeta del diario (o un .md suelto)")
    cli.add_argument("--salida", type=Path, default=Path("derivado/visor.html"))
    cli.add_argument("--no-abrir", action="store_true", help="genera pero no abre el navegador")
    args = cli.parse_args(argv)

    if not args.ruta.exists():
        print(f"no existe: {args.ruta}", file=sys.stderr)
        return 2

    dias = leer_vault(args.ruta)
    if not dias:
        print(f"no se encontró ninguna nota YYYY-MM-DD.md en {args.ruta}")
        return 1

    salida = generar(tabla_dias(dias), tabla_ingestas(dias),
                     args.salida, str(args.ruta.resolve()))
    ingestas = sum(len(d.ingestas) for d in dias)
    print(f"{len(dias)} día(s) · {ingestas} ingesta(s) → {salida.resolve()}")
    if not args.no_abrir:
        webbrowser.open(salida.resolve().as_uri())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
