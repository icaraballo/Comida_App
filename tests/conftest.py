"""Los fixtures viven en el vault, no aquí.

Son el contrato de aceptación y pertenecen a la documentación (junto a
`fixtures/README.md`, que explica qué prueba cada uno). Copiarlos a este repo
crearía dos versiones del contrato que divergirían a la primera.

Se resuelven por convención (el vault, al lado de este repo) y se puede apuntar
a otro sitio con la variable de entorno COMIDA_FIXTURES.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

POR_DEFECTO = RAIZ.parent / "Vault Proyectos" / "Comida_App" / "fixtures"


def ruta_fixtures() -> Path:
    return Path(os.environ.get("COMIDA_FIXTURES", POR_DEFECTO))


@pytest.fixture(scope="session")
def fixtures() -> Path:
    ruta = ruta_fixtures()
    if not ruta.is_dir():
        pytest.skip(
            f"no se encuentran los fixtures en {ruta}. "
            "Están en el vault; apuntar con COMIDA_FIXTURES=<ruta>"
        )
    return ruta
