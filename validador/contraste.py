"""Segunda pasada opcional contra `esquema/dia.schema.json` (`validar.py --schema`).

Las reglas de reglas.py son la herramienta de trabajo: dan linea y sugerencia.
Esta pasada existe para que el JSON Schema no sea papel mojado — si el contrato
publicado y las reglas se separan, esto lo canta. No sustituye a nada.

Requiere `jsonschema`. Sin el, no falla: avisa y sigue.
"""

from __future__ import annotations

import datetime as dt

import yaml

import esquema
from validador import nota as N
from validador.hallazgos import AVISO, ERROR, Hallazgo


def _jsonificar(valor, campo: str | None = None):
    """YAML da fechas y booleanos donde el .md tenia texto; se deshace aqui.

    El JSON Schema describe lo que hay ESCRITO en la nota, asi que este puente
    tiene que devolver eso mismo: `hambre_antes: no` vuelve a ser "no" y no False
    (ver esquema.destrampar). Si no, el contraste denunciaria un fallo que no
    esta en el fichero sino en el lector.
    """
    if isinstance(valor, dt.datetime):
        return valor.isoformat()
    if isinstance(valor, dt.date):
        return valor.isoformat()
    if isinstance(valor, dict):
        return {str(k): _jsonificar(v, str(k)) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_jsonificar(v, campo) for v in valor]
    return esquema.destrampar(valor, esquema.vocabulario_de_campo().get(campo or ""))


def contrastar(texto: str, nombre_fichero: str) -> list[Hallazgo]:
    try:
        import jsonschema
    except ImportError:
        return [Hallazgo(AVISO, "sin_jsonschema", 1,
                         "no se pudo cruzar con el JSON Schema: falta el paquete `jsonschema`",
                         "pip install jsonschema", nombre_fichero)]

    nota = N.leer(texto, nombre_fichero)
    if nota.sin_frontmatter or nota.error_yaml or nota.frontmatter is None:
        return []  # ya lo reporta reglas.py, con mejor mensaje

    try:
        datos = _jsonificar(yaml.safe_load(yaml.serialize(nota.frontmatter)))
    except yaml.YAMLError:
        return []
    if not isinstance(datos, dict):
        return []

    validador = jsonschema.Draft202012Validator(esquema.schema())
    hallazgos = []
    for fallo in sorted(validador.iter_errors(datos), key=lambda e: list(e.path)):
        ruta = "/".join(str(p) for p in fallo.path) or "(raiz)"
        hallazgos.append(Hallazgo(ERROR, "schema", 1,
                                  f"[schema] {ruta}: {fallo.message}",
                                  None, nombre_fichero))
    return hallazgos
