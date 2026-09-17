#!/usr/bin/env python3
"""Valida las notas de diario de un vault.

    python validar.py <ruta>              un fichero o una carpeta
    python validar.py <ruta> --solo-errores
    python validar.py <ruta> --json
    python validar.py <ruta> --schema     cruza ademas con esquema/dia.schema.json

Sale con codigo 1 si hay errores. Los avisos no hacen fallar nada: avisar de un
campo ausente no es lo mismo que rechazar la entrada (principio 3 de Instrucciones).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validador.hallazgos import AVISO, ERROR, Hallazgo  # noqa: E402
from validador.reglas import validar  # noqa: E402


def notas(ruta: Path) -> list[Path]:
    if ruta.is_file():
        return [ruta]
    return sorted(p for p in ruta.rglob("*.md") if not p.name.startswith("_"))


def revisar(ficheros: list[Path], con_schema: bool) -> list[Hallazgo]:
    hallazgos: list[Hallazgo] = []
    for fichero in ficheros:
        texto = fichero.read_text(encoding="utf-8")
        propios = validar(texto, fichero.name)
        if con_schema:
            from validador.contraste import contrastar
            propios += contrastar(texto, fichero.name)
        hallazgos += propios
    return hallazgos


def main(argv: list[str] | None = None) -> int:
    cli = argparse.ArgumentParser(description="Valida notas de diario del registro.")
    cli.add_argument("ruta", type=Path, help="fichero .md o carpeta del diario")
    cli.add_argument("--solo-errores", action="store_true", help="oculta los avisos")
    cli.add_argument("--json", action="store_true", dest="como_json", help="salida en JSON")
    cli.add_argument("--schema", action="store_true",
                     help="cruza ademas con el JSON Schema (requiere jsonschema)")
    args = cli.parse_args(argv)

    if not args.ruta.exists():
        print(f"no existe: {args.ruta}", file=sys.stderr)
        return 2

    ficheros = notas(args.ruta)
    hallazgos = revisar(ficheros, args.schema)
    hallazgos.sort(key=lambda h: (h.fichero, h.linea, h.nivel != ERROR, h.codigo))

    errores = [h for h in hallazgos if h.nivel == ERROR]
    avisos = [h for h in hallazgos if h.nivel == AVISO]
    mostrados = errores if args.solo_errores else hallazgos

    if args.como_json:
        print(json.dumps({
            "ficheros": len(ficheros),
            "errores": len(errores),
            "avisos": len(avisos),
            "hallazgos": [h.como_dict() for h in mostrados],
        }, ensure_ascii=False, indent=2))
        return 1 if errores else 0

    for hallazgo in mostrados:
        print(hallazgo.linea_texto())
    if mostrados:
        print()
    resumen = f"{len(ficheros)} nota(s) · {len(errores)} error(es) · {len(avisos)} aviso(s)"
    print(resumen)
    if not errores:
        print("sin errores: el vault se puede parsear")
    return 1 if errores else 0


if __name__ == "__main__":
    raise SystemExit(main())
