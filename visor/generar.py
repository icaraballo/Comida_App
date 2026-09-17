"""Genera la página del visor."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from visor.datos import construir
from visor.plantilla import PAGINA


def generar(marco_dias: pd.DataFrame, marco_ingestas: pd.DataFrame,
            destino: Path, origen: str) -> Path:
    datos = construir(marco_dias, marco_ingestas, origen)
    # `</script>` dentro del JSON cerraría la etiqueta antes de tiempo.
    crudo = json.dumps(datos, ensure_ascii=False).replace("</", "<\\/")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(PAGINA.replace("__DATOS__", crudo), encoding="utf-8")
    return destino
