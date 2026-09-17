"""Escribe la capa derivada: parquet y SQLite.

Las dos salidas son **regenerables desde cero** y nunca se editan a mano (D1).
Si se pierden, no se pierde nada: el dato está en los `.md`.

Parquet conserva las listas tal cual. SQLite no tiene tipo lista, así que además
de guardarlas como texto se despliega una tabla larga `emociones`, que es la
forma en la que Q1 y Q2 quieren los datos y la que Power BI sabe cruzar.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pandas as pd

LISTAS = ("emociones_antes", "emociones_despues", "sintomas",
          "emociones_aparecen", "emociones_desaparecen")


def tabla_emociones(ingestas: pd.DataFrame) -> pd.DataFrame:
    """Formato largo: una fila por (ingesta, momento, emoción)."""
    filas = []
    for _, fila in ingestas.iterrows():
        for momento, columna in (("antes", "emociones_antes"), ("despues", "emociones_despues")):
            for emocion in fila.get(columna) or []:
                filas.append({
                    "fecha": fila["fecha"],
                    "hora": fila["hora"],
                    "tipo": fila["tipo"],
                    "momento": momento,
                    "emocion": emocion,
                    "hambre_antes": fila.get("hambre_antes"),
                })
    return pd.DataFrame(filas, columns=["fecha", "hora", "tipo", "momento",
                                        "emocion", "hambre_antes"])


def _para_sqlite(marco: pd.DataFrame) -> pd.DataFrame:
    copia = marco.copy()
    for columna in LISTAS:
        if columna in copia.columns:
            copia[columna] = copia[columna].apply(
                lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, list) else None
            )
    for columna in copia.columns:
        if copia[columna].map(lambda v: isinstance(v, (dict, list))).any():
            copia[columna] = copia[columna].apply(
                lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
            )
    return copia


def exportar(dias: pd.DataFrame, ingestas: pd.DataFrame, destino: Path) -> dict[str, Path]:
    """Escribe parquet y SQLite en `destino`. Devuelve qué se escribió."""
    destino.mkdir(parents=True, exist_ok=True)
    emociones = tabla_emociones(ingestas)

    salidas = {}
    for nombre, marco in (("dias", dias), ("ingestas", ingestas), ("emociones", emociones)):
        ruta = destino / f"{nombre}.parquet"
        marco.to_parquet(ruta, index=False)
        salidas[f"{nombre}.parquet"] = ruta

    base = destino / "registro.sqlite"
    if base.exists():
        base.unlink()  # se regenera entera: nunca se escribe encima (D1)
    with sqlite3.connect(base) as conexion:
        for nombre, marco in (("dias", dias), ("ingestas", ingestas), ("emociones", emociones)):
            _para_sqlite(marco).to_sql(nombre, conexion, index=False, if_exists="replace")
    salidas["registro.sqlite"] = base
    return salidas
