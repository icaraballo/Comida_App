"""La capa derivada: una fila por ingesta, más una tabla de días.

Dos tablas, no una, y el motivo está en Fixtures (`2026-09-18`): un día sin
ingestas produce **cero filas** de ingesta pero **sí** tiene que contar como día
registrado. Si sólo existiera la tabla de ingestas, cualquier tasa por día
saldría inflada, porque el denominador se habría comido los días flojos.

Esta capa es regenerable desde cero y nunca se edita a mano (D1).
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

from parser.lector import Dia, minutos

# Orden de las columnas: primero el día (desnormalizado), luego la ingesta, luego
# lo calculado. Que se lea de izquierda a derecha como se registró.
COLUMNAS_DIA = ["fecha", "dia_semana", "agua_litros", "actividad", "actividad_horas", "sueno_horas", "sueno_calidad"]
COLUMNAS_INGESTA = [
    "tipo", "hora", "alimentos", "hambre_antes",
    "emociones_antes", "pensamientos_antes",
    "emociones_despues", "pensamientos_despues",
    "energia", "sintomas",
    "compania", "lugar", "pantalla",
    "emocion_otra_antes", "emocion_otra_despues", "energia_otro", "sintoma_otros",
]
COLUMNAS_DERIVADAS = [
    "orden", "minuto", "hueco_min", "madrugada",
    "n_emociones_antes", "n_emociones_despues",
    "emociones_aparecen", "emociones_desaparecen",
]

MADRUGADA_HASTA = 5 * 60  # 05:00


def _lista(valor) -> list[str]:
    if isinstance(valor, list):
        return [v for v in valor if isinstance(v, str)]
    return []


def tabla_dias(dias: list[Dia]) -> pd.DataFrame:
    """Una fila por nota de diario. Incluye los días sin ingestas."""
    filas = []
    for dia in dias:
        filas.append({
            "fecha": dia.fecha,
            "dia_semana": dia.fecha.weekday(),
            "fichero": dia.fichero,
            "n_ingestas": len(dia.ingestas),
            "registrado": dia.registrado,
            **{c: dia.campos.get(c) for c in ("agua_litros", "actividad", "actividad_horas",
                                              "sueno_horas", "sueno_calidad")},
            **{c: dia.secciones.get(c) for c in ("reflexiones", "pensamientos_predominantes",
                                                 "orgullo_y_gratitud")},
        })
    return pd.DataFrame(filas)


def tabla_ingestas(dias: list[Dia]) -> pd.DataFrame:
    """Una fila por ingesta, con los campos del día repetidos y lo calculado."""
    filas = []
    for dia in dias:
        # Se ordena por hora aquí: el fichero no garantiza el orden (Esquema de
        # datos, caso límite 4) y todo lo que viene después depende de él.
        ordenadas = sorted(
            dia.ingestas,
            key=lambda i: (minutos(i.get("hora")) is None, minutos(i.get("hora")) or 0),
        )
        anterior: int | None = None
        for orden, ingesta in enumerate(ordenadas, start=1):
            minuto = minutos(ingesta.get("hora"))
            contexto = ingesta.get("contexto") or {}
            antes = _lista(ingesta.get("emociones_antes"))
            despues = _lista(ingesta.get("emociones_despues"))

            # La primera ingesta del día tiene hueco nulo, NUNCA 0: un 0 diría
            # "comió dos veces seguidas", y lo cierto es que no se sabe.
            hueco = None
            if minuto is not None and anterior is not None:
                hueco = minuto - anterior

            filas.append({
                "fecha": dia.fecha,
                "dia_semana": dia.fecha.weekday(),
                **{c: dia.campos.get(c) for c in ("agua_litros", "actividad", "actividad_horas",
                                                  "sueno_horas", "sueno_calidad")},
                "tipo": ingesta.get("tipo"),
                "hora": ingesta.get("hora"),
                "alimentos": ingesta.get("alimentos"),
                "hambre_antes": ingesta.get("hambre_antes"),
                "emociones_antes": antes,
                "pensamientos_antes": ingesta.get("pensamientos_antes"),
                "emociones_despues": despues,
                "pensamientos_despues": ingesta.get("pensamientos_despues"),
                "energia": ingesta.get("energia"),
                "sintomas": _lista(ingesta.get("sintomas")),
                "compania": contexto.get("compania"),
                "lugar": contexto.get("lugar"),
                "pantalla": contexto.get("pantalla"),
                "emocion_otra_antes": ingesta.get("emocion_otra_antes"),
                "emocion_otra_despues": ingesta.get("emocion_otra_despues"),
                "energia_otro": ingesta.get("energia_otro"),
                "sintoma_otros": ingesta.get("sintoma_otros"),
                "orden": orden,
                "minuto": minuto,
                "hueco_min": hueco,
                "madrugada": None if minuto is None else minuto < MADRUGADA_HASTA,
                "n_emociones_antes": len(antes) or None,
                "n_emociones_despues": len(despues) or None,
                # El delta completo es la matriz de transición de Q2, que es
                # capa de análisis. Aquí sólo lo que es puramente de la fila.
                "emociones_aparecen": sorted(set(despues) - set(antes)),
                "emociones_desaparecen": sorted(set(antes) - set(despues)),
            })
            if minuto is not None:
                anterior = minuto

    columnas = COLUMNAS_DIA[:2] + COLUMNAS_DIA[2:] + COLUMNAS_INGESTA + COLUMNAS_DERIVADAS
    marco = pd.DataFrame(filas)
    if marco.empty:
        return pd.DataFrame(columns=columnas)
    return marco[[c for c in columnas if c in marco.columns]]
