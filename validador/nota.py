"""Lectura de una nota de diario: frontmatter YAML + cuerpo, con nº de línea.

Se trabaja sobre el arbol de nodos de PyYAML (`yaml.compose`) en vez de sobre el
dict que devuelve `safe_load`. Dos motivos, y los dos son el nucleo del proyecto:

- `safe_load` pierde la posicion: sin numero de linea, corregir es buscar a mano.
- `safe_load` ya ha convertido el valor: `hora: 8:15` llega como el entero 495 y
  el error mas traicionero del formato se vuelve invisible. Con el nodo crudo se
  ve la etiqueta que PyYAML resolvio y el texto original.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import yaml

TAG_STR = "tag:yaml.org,2002:str"
TAG_INT = "tag:yaml.org,2002:int"
TAG_FLOAT = "tag:yaml.org,2002:float"
TAG_BOOL = "tag:yaml.org,2002:bool"
TAG_NULL = "tag:yaml.org,2002:null"
TAG_TIMESTAMP = "tag:yaml.org,2002:timestamp"


@dataclass
class Nota:
    """Una nota ya troceada. `frontmatter` es el nodo raiz (o None)."""

    nombre: str
    frontmatter: yaml.Node | None = None
    secciones: dict[str, str] = field(default_factory=dict)
    error_yaml: tuple[int, str] | None = None
    sin_frontmatter: bool = False


def linea(nodo: yaml.Node) -> int:
    """Linea del fichero, 1-indexada. El offset del frontmatter ya va incluido."""
    return nodo.start_mark.line + 1


def es_escalar(nodo: yaml.Node) -> bool:
    return isinstance(nodo, yaml.ScalarNode)


def es_nulo(nodo: yaml.Node) -> bool:
    return isinstance(nodo, yaml.ScalarNode) and nodo.tag == TAG_NULL


def pares(nodo: yaml.Node) -> list[tuple[yaml.ScalarNode, yaml.Node]]:
    """Pares clave/valor en orden de fichero. Conserva las claves repetidas."""
    if not isinstance(nodo, yaml.MappingNode):
        return []
    return [(k, v) for k, v in nodo.value if isinstance(k, yaml.ScalarNode)]


def elementos(nodo: yaml.Node) -> list[yaml.Node]:
    if not isinstance(nodo, yaml.SequenceNode):
        return []
    return list(nodo.value)


_CONSTRUCTOR = yaml.constructor.SafeConstructor()


def valor(nodo: yaml.Node):
    """Valor Python del nodo, con el tipo que PyYAML ya resolvio.

    Se construye desde la etiqueta del nodo, no reserializando: asi el valor es
    exactamente el que habria visto `safe_load` (incluido el 495 de `hora: 8:15`).
    """
    try:
        return _CONSTRUCTOR.construct_object(nodo, deep=True)
    except yaml.YAMLError:
        return None


def texto_crudo(nodo: yaml.Node) -> str:
    """Lo que hay escrito en el fichero, antes de convertir nada."""
    return nodo.value if isinstance(nodo, yaml.ScalarNode) else ""


def leer(texto: str, nombre: str) -> Nota:
    """Trocea el fichero. No valida nada: eso es cosa de reglas.py."""
    lineas = texto.splitlines()
    if not lineas or lineas[0].strip() != "---":
        return Nota(nombre=nombre, sin_frontmatter=True)

    cierre = next((i for i, l in enumerate(lineas[1:], start=1) if l.strip() == "---"), None)
    if cierre is None:
        return Nota(nombre=nombre, sin_frontmatter=True)

    # Se rellena con lineas en blanco para que las marcas de PyYAML caigan
    # directamente sobre el numero de linea real del fichero.
    crudo = "\n".join([""] + lineas[1:cierre])
    nota = Nota(nombre=nombre, secciones=_secciones(lineas[cierre + 1 :]))
    try:
        nota.frontmatter = yaml.compose(crudo)
    except yaml.MarkedYAMLError as err:
        marca = err.problem_mark
        nota.error_yaml = ((marca.line + 1) if marca else 1, err.problem or str(err))
    except yaml.YAMLError as err:
        nota.error_yaml = (1, str(err))
    return nota


def _secciones(lineas_cuerpo: list[str]) -> dict[str, str]:
    """Cuerpo troceado por encabezado `##`. Sin normalizar: reglas.py decide."""
    secciones: dict[str, str] = {}
    actual: str | None = None
    acumulado: list[str] = []
    for linea_texto in lineas_cuerpo:
        if linea_texto.startswith("## "):
            if actual is not None:
                secciones[actual] = "\n".join(acumulado).strip()
            actual = linea_texto[3:].strip()
            acumulado = []
        elif actual is not None:
            acumulado.append(linea_texto)
    if actual is not None:
        secciones[actual] = "\n".join(acumulado).strip()
    return secciones
