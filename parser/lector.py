"""De un `.md` a un diccionario limpio.

Reutiliza el troceador del validador (`validador.nota`) para no tener dos formas
distintas de leer la misma nota. La diferencia de intención:

- el validador mira el árbol de nodos porque necesita el número de línea;
- el parser sólo quiere los valores, así que aquí se aplanan a Python normal.

Lo que está roto NO se inventa: un campo que no se entiende se queda en `None` y
la fila sale igualmente. Un registro parcial vale infinitamente más que ninguno
(principio 3 de Instrucciones, D4 en Decisiones).
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

import esquema
from validador import nota as N

RE_NOMBRE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
RE_HORA = re.compile(r"^(\d{1,2}):(\d{2})$")

CAMPOS_DIA = ("agua_litros", "actividad", "actividad_horas", "sueno_horas", "sueno_calidad")
SECCIONES = {
    "reflexiones": "reflexiones",
    "pensamientos_predominantes": "pensamientos_predominantes",
    "orgullo_y_gratitud": "orgullo_y_gratitud",
}


@dataclass
class Dia:
    fecha: dt.date
    fichero: str
    ingestas: list[dict] = field(default_factory=list)
    campos: dict = field(default_factory=dict)
    secciones: dict = field(default_factory=dict)

    @property
    def registrado(self) -> bool:
        """Un día sin ingestas cuenta como día registrado si tiene algo escrito.

        Importa para las tasas por día: si los días vacíos no se cuentan, todas
        las frecuencias salen infladas (ver Fixtures, 2026-09-18).
        """
        return bool(self.ingestas or self.campos or any(self.secciones.values()))


def _valor_plano(nodo, campo: str | None = None):
    """Nodo YAML → valor Python, deshaciendo las trampas de YAML 1.1."""
    if nodo is None or N.es_nulo(nodo):
        return None
    if isinstance(nodo, yaml.SequenceNode):
        return [_valor_plano(e, campo) for e in N.elementos(nodo)]
    if isinstance(nodo, yaml.MappingNode):
        return {k.value: _valor_plano(v, k.value) for k, v in N.pares(nodo)}
    bruto = N.valor(nodo)
    return esquema.destrampar(bruto, esquema.vocabulario_de_campo().get(campo or ""))


def leer_dia(ruta: Path) -> Dia | None:
    """Lee una nota. Devuelve None si no es una nota de diario parseable."""
    coincide = RE_NOMBRE.match(ruta.name)
    if not coincide:
        return None
    nota = N.leer(ruta.read_text(encoding="utf-8"), ruta.name)
    if nota.sin_frontmatter or nota.error_yaml or nota.frontmatter is None:
        return None
    if not isinstance(nota.frontmatter, yaml.MappingNode):
        return None

    # Manda el nombre del fichero, siempre (Esquema de datos, caso límite 5).
    fecha = dt.date.fromisoformat(coincide.group(1))
    crudo = {k.value: v for k, v in N.pares(nota.frontmatter)}

    dia = Dia(fecha=fecha, fichero=ruta.name)
    for campo in CAMPOS_DIA:
        valor = _valor_plano(crudo.get(campo), campo)
        if valor is not None:
            dia.campos[campo] = valor

    for titulo, texto in nota.secciones.items():
        clave = SECCIONES.get(esquema.normalizar(titulo))
        if clave and texto:
            dia.secciones[clave] = texto

    ingestas = _valor_plano(crudo.get("ingestas"), "ingestas") or []
    if isinstance(ingestas, list):
        dia.ingestas = [i for i in ingestas if isinstance(i, dict)]
    return dia


def minutos(hora) -> int | None:
    """"HH:MM" → minutos desde medianoche. None si no se entiende."""
    if not isinstance(hora, str):
        return None
    coincide = RE_HORA.match(hora.strip())
    if not coincide:
        return None
    h, m = int(coincide.group(1)), int(coincide.group(2))
    if h > 23 or m > 59:
        return None
    return h * 60 + m


def leer_vault(raiz: Path) -> list[Dia]:
    """Todos los días de una carpeta, ordenados por fecha."""
    ficheros = [raiz] if raiz.is_file() else sorted(raiz.rglob("*.md"))
    dias = [d for d in (leer_dia(f) for f in ficheros) if d is not None]
    return sorted(dias, key=lambda d: d.fecha)
