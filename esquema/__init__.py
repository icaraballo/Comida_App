"""Carga del contrato de datos.

`dia.schema.json` es la unica fuente de los vocabularios cerrados en codigo.
Nadie escribe una lista de enums a mano en otro sitio: se leen de aqui.
"""

from __future__ import annotations

import json
import unicodedata
from functools import lru_cache
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
RUTA_SCHEMA = RAIZ / "dia.schema.json"
RUTA_SINONIMOS = RAIZ / "sinonimos.json"


@lru_cache(maxsize=1)
def schema() -> dict:
    return json.loads(RUTA_SCHEMA.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def vocabularios() -> dict[str, tuple[str, ...]]:
    """{'emocion': ('felicidad', ...), ...} tal y como estan en el schema."""
    defs = schema()["$defs"]
    return {
        nombre: tuple(cuerpo["enum"])
        for nombre, cuerpo in defs.items()
        if "enum" in cuerpo
    }


@lru_cache(maxsize=1)
def sinonimos() -> dict[str, dict[str, tuple[str, ...]]]:
    crudo = json.loads(RUTA_SINONIMOS.read_text(encoding="utf-8"))
    return {
        vocab: {normalizar(k): tuple(v) for k, v in mapa.items()}
        for vocab, mapa in crudo.items()
        if vocab != "_nota"
    }


def normalizar(valor: str) -> str:
    """minusculas, sin acentos, espacios y guiones a guion bajo.

    Es la forma canonica de los valores (D5). Sirve para detectar que
    'Hinchazon' y 'hinchazón' son el mismo valor mal escrito, no otro valor.
    """
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", valor) if unicodedata.category(c) != "Mn"
    )
    return sin_tildes.strip().lower().replace(" ", "_").replace("-", "_")


# --- Campos, leidos tambien del schema para no duplicarlos ---

def campos_dia() -> tuple[str, ...]:
    return tuple(schema()["properties"])


def campos_obligatorios_dia() -> tuple[str, ...]:
    return tuple(schema().get("required", ()))


def campos_ingesta() -> tuple[str, ...]:
    return tuple(schema()["$defs"]["ingesta"]["properties"])


def campos_obligatorios_ingesta() -> tuple[str, ...]:
    return tuple(schema()["$defs"]["ingesta"].get("required", ()))


def campos_contexto() -> tuple[str, ...]:
    return tuple(schema()["$defs"]["contexto"]["properties"])


# --- La trampa de los booleanos de YAML 1.1 ---
#
# Hermana de la de `hora: 8:15`. PyYAML resuelve `no` sin comillas como el
# booleano False (su lista incluye yes/no/on/off), y el vocabulario `hambre`
# tiene `no` como valor. Quien escribe `hambre_antes: no` en el .md quiso decir
# la cadena "no"; el contrato lo describe el markdown, no lo que devuelve PyYAML.
# Todo lo que lee notas deshace la trampa por aqui, en un unico sitio.
BOOLEANOS_YAML = {False: "no", True: "si"}


def destrampar(valor, vocabulario: str | None):
    """Devuelve el valor tal y como estaba escrito en el .md."""
    if vocabulario and isinstance(valor, bool) and valor in BOOLEANOS_YAML:
        candidato = BOOLEANOS_YAML[valor]
        if candidato in vocabularios()[vocabulario]:
            return candidato
    return valor


@lru_cache(maxsize=1)
def vocabulario_de_campo() -> dict[str, str]:
    """{'hambre_antes': 'hambre', 'emociones_antes': 'emocion', ...}

    Derivado de los `$ref` del schema: no hay una segunda lista que mantener.
    """
    mapa: dict[str, str] = {}
    s = schema()
    contenedores = [s, s["$defs"]["ingesta"], s["$defs"]["contexto"]]
    for contenedor in contenedores:
        for campo, cuerpo in contenedor.get("properties", {}).items():
            destino = cuerpo.get("$ref") or cuerpo.get("items", {}).get("$ref")
            if destino and destino.startswith("#/$defs/"):
                nombre = destino.rsplit("/", 1)[1]
                if "enum" in s["$defs"][nombre]:
                    mapa[campo] = nombre
    return mapa
