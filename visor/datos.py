"""Prepara los datos que consume el visor.

Se construye desde la capa derivada, no desde los `.md`: así lo que se ve en
pantalla es exactamente lo que verá el análisis. Si algo se ve raro en el visor,
está raro en los datos, no en la vista.
"""

from __future__ import annotations

import datetime as dt
import math

import pandas as pd

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]
MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio",
         "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"]


def _limpio(valor):
    """NaN, NaT y demás ausencias → None. Un ausente se queda ausente: no se
    imputa nada, porque imputar fabrica datos que nunca se registraron (D4)."""
    if valor is None:
        return None
    if isinstance(valor, float) and math.isnan(valor):
        return None
    if isinstance(valor, (dt.date, dt.datetime)):
        return valor.isoformat()[:10]
    if isinstance(valor, (list, tuple)):
        return [_limpio(v) for v in valor]
    if pd.isna(valor) if not isinstance(valor, (list, tuple, dict)) else False:
        return None
    return valor


def construir(marco_dias: pd.DataFrame, marco_ingestas: pd.DataFrame, origen: str) -> dict:
    por_fecha: dict[str, list[dict]] = {}
    for _, fila in marco_ingestas.iterrows():
        fecha = _limpio(fila["fecha"])
        por_fecha.setdefault(fecha, []).append({
            campo: _limpio(fila.get(campo)) for campo in (
                "orden", "tipo", "hora", "alimentos", "hambre_antes",
                "emociones_antes", "pensamientos_antes",
                "emociones_despues", "pensamientos_despues",
                "energia", "sintomas", "compania", "lugar", "pantalla",
                "emocion_otra_antes", "emocion_otra_despues",
                "energia_otro", "sintoma_otros",
                "hueco_min", "madrugada",
            )
        })

    dias = []
    for _, fila in marco_dias.iterrows():
        fecha = _limpio(fila["fecha"])
        dias.append({
            "fecha": fecha,
            "dia_semana": int(fila["dia_semana"]),
            "n_ingestas": int(fila["n_ingestas"]),
            **{campo: _limpio(fila.get(campo)) for campo in (
                "agua_litros", "actividad", "actividad_horas", "sueno_horas", "sueno_calidad",
                "reflexiones", "pensamientos_predominantes", "orgullo_y_gratitud")},
            "ingestas": por_fecha.get(fecha, []),
        })

    fechas = [d["fecha"] for d in dias]
    return {
        "generado": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "origen": origen,
        "desde": min(fechas) if fechas else None,
        "hasta": max(fechas) if fechas else None,
        "dias": dias,
        "dias_semana": DIAS_SEMANA,
        "meses": MESES,
    }
