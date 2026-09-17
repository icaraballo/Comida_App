"""Lo que el validador reporta.

Dos niveles y la diferencia entre ellos es el principio 3 de CLAUDE.md:

- ERROR: el dato esta roto o no se puede interpretar. Hay que tocar el .md.
- AVISO: el dato es valido pero falta algo o hay una ambiguedad. Se puede vivir
  con ello indefinidamente. Un dia registrado a medias es un dia registrado.

El validador NUNCA rechaza una entrada: reporta y sigue.
"""

from __future__ import annotations

from dataclasses import dataclass

ERROR = "ERROR"
AVISO = "AVISO"


@dataclass(frozen=True)
class Hallazgo:
    nivel: str
    codigo: str
    linea: int
    mensaje: str
    sugerencia: str | None = None
    fichero: str = ""

    def linea_texto(self) -> str:
        cola = f" — {self.sugerencia}" if self.sugerencia else ""
        return f"{self.fichero}:{self.linea}: {self.nivel} [{self.codigo}] {self.mensaje}{cola}"

    def como_dict(self) -> dict:
        return {
            "fichero": self.fichero,
            "linea": self.linea,
            "nivel": self.nivel,
            "codigo": self.codigo,
            "mensaje": self.mensaje,
            "sugerencia": self.sugerencia,
        }
