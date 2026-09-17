"""Contrato de aceptación del parser.

Los casos límite salen de `fixtures/README.md` y de Esquema de datos § *Casos
límite que el parser debe resolver*, en el vault.
"""

from __future__ import annotations

import pytest

from parser.lector import leer_vault, minutos
from parser.tidy import tabla_dias, tabla_ingestas


@pytest.fixture(scope="module")
def dias(fixtures):
    return leer_vault(fixtures / "diario")


@pytest.fixture(scope="module")
def ingestas(dias):
    return tabla_ingestas(dias)


def _dia(marco, fecha):
    return marco[marco["fecha"].astype(str) == fecha]


# --------------------------------------------------------------------------
# Casos límite del esquema
# --------------------------------------------------------------------------

def test_una_fila_por_ingesta(ingestas):
    assert len(ingestas) == 5 + 5 + 3 + 4 + 0


def test_el_dia_sin_ingestas_da_cero_filas_pero_cuenta_como_dia(dias, ingestas):
    """Si no contara, todas las tasas por día saldrían infladas."""
    assert _dia(ingestas, "2026-09-18").empty
    marco = tabla_dias(dias)
    assert len(marco) == 5
    assert bool(_dia(marco, "2026-09-18")["registrado"].iloc[0])


def test_las_ingestas_desordenadas_se_ordenan(ingestas):
    """En el fichero vienen cena, picoteo, desayuno, comida."""
    horas = list(_dia(ingestas, "2026-09-17")["hora"])
    assert horas == ["00:40", "09:00", "14:30", "21:15"]


def test_la_madrugada_pertenece_a_su_fichero_y_se_marca(ingestas):
    """00:40 no se reasigna al día anterior, pero queda marcada para filtrarla."""
    fila = _dia(ingestas, "2026-09-17").iloc[0]
    assert fila["hora"] == "00:40"
    assert fila["madrugada"] is True or bool(fila["madrugada"])
    assert not bool(_dia(ingestas, "2026-09-17").iloc[1]["madrugada"])


def test_la_primera_ingesta_del_dia_tiene_hueco_nulo_nunca_cero(ingestas):
    """Un 0 diría 'comió dos veces seguidas'. La verdad es que no se sabe."""
    import pandas as pd
    for fecha in ("2026-09-14", "2026-09-15", "2026-09-16", "2026-09-17"):
        primera = _dia(ingestas, fecha).iloc[0]
        assert pd.isna(primera["hueco_min"]), fecha


def test_hueco_min_del_fixture(ingestas):
    """440 min entre el desayuno (07:50) y la comida (15:10). Lo dice el contrato."""
    fila = _dia(ingestas, "2026-09-15")
    assert fila[fila["hora"] == "15:10"]["hueco_min"].iloc[0] == 440


def test_dos_ingestas_del_mismo_tipo_el_mismo_dia(ingestas):
    """La lista es abierta (D3): dos picoteos en un día son válidos."""
    picoteos = _dia(ingestas, "2026-09-15")["tipo"].tolist().count("picoteo")
    assert picoteos == 2


def test_el_dia_minimo_produce_filas_utiles(ingestas):
    """Sólo tipo + hora + alimentos. Tiene que salir igual, con nulos."""
    import pandas as pd
    filas = _dia(ingestas, "2026-09-16")
    assert len(filas) == 3
    assert filas["alimentos"].notna().all()
    assert pd.isna(filas["energia"]).all()


def test_no_se_imputan_valores_ausentes(ingestas):
    """Un campo ausente se queda ausente: imputar fabrica datos (D4)."""
    import pandas as pd
    fila = _dia(ingestas, "2026-09-16").iloc[0]
    assert pd.isna(fila["hambre_antes"])
    assert fila["emociones_antes"] == []


def test_hambre_no_llega_como_texto_no_como_booleano(ingestas):
    """La trampa de YAML 1.1: `no` sin comillas es False."""
    valores = set(_dia(ingestas, "2026-09-15")["hambre_antes"].dropna())
    assert valores <= {"si", "algo", "no"}
    assert "no" in valores


def test_manda_el_nombre_del_fichero(dias):
    assert [str(d.fecha) for d in dias] == [d.fichero[:-3] for d in dias]


# --------------------------------------------------------------------------
# Derivados
# --------------------------------------------------------------------------

def test_dia_semana(ingestas):
    assert _dia(ingestas, "2026-09-14")["dia_semana"].iloc[0] == 0  # lunes


def test_delta_emocional(ingestas):
    """El picoteo de las 17:40: ansiedad + aburrimiento → culpa."""
    fila = _dia(ingestas, "2026-09-15")
    fila = fila[fila["hora"] == "17:40"].iloc[0]
    assert fila["emociones_aparecen"] == ["culpa"]
    assert sorted(fila["emociones_desaparecen"]) == ["aburrimiento", "ansiedad"]
    assert fila["n_emociones_antes"] == 2


def test_contexto_parcial_es_valido(ingestas):
    """La ingesta de madrugada sólo trae `lugar`."""
    import pandas as pd
    fila = _dia(ingestas, "2026-09-17").iloc[0]
    assert fila["lugar"] == "casa"
    assert pd.isna(fila["compania"])


@pytest.mark.parametrize("hora,esperado", [
    ("00:40", 40), ("08:15", 495), ("23:59", 1439),
    ("25:70", None), ("ocho", None), (495, None), (None, None),
])
def test_minutos(hora, esperado):
    assert minutos(hora) == esperado


# --------------------------------------------------------------------------
# Exportación y visor
# --------------------------------------------------------------------------

def test_exportar_y_releer(dias, ingestas, tmp_path):
    import pandas as pd
    from parser.exportar import exportar
    salidas = exportar(tabla_dias(dias), ingestas, tmp_path)
    assert set(salidas) == {"dias.parquet", "ingestas.parquet",
                            "emociones.parquet", "registro.sqlite"}
    releido = pd.read_parquet(salidas["ingestas.parquet"])
    assert len(releido) == len(ingestas)


def test_tabla_larga_de_emociones(ingestas):
    """Formato que piden Q1 y Q2: una fila por (ingesta, momento, emoción)."""
    from parser.exportar import tabla_emociones
    larga = tabla_emociones(ingestas)
    assert set(larga["momento"]) == {"antes", "despues"}
    assert not larga.empty


def test_el_visor_es_autocontenido(dias, ingestas, tmp_path):
    """Sin CDN, sin fuentes remotas, sin una sola petición de red (D9)."""
    from visor.generar import generar
    salida = generar(tabla_dias(dias), ingestas, tmp_path / "visor.html", "test")
    html = salida.read_text(encoding="utf-8")
    assert "<script src=" not in html
    assert "http://" not in html and "https://" not in html
    assert "2026-09-15" in html


def test_el_visor_no_pinta_patrones(dias, ingestas, tmp_path):
    """Nada de gráficos antes de 4-6 semanas (Análisis § Reglas del análisis)."""
    from visor.generar import generar
    html = generar(tabla_dias(dias), ingestas, tmp_path / "v.html", "test").read_text("utf-8")
    assert "<canvas" not in html and "<svg" not in html
