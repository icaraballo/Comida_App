"""Contrato de aceptación del validador.

Lo que se comprueba aquí está escrito en `fixtures/README.md` del vault. Si un
cambio rompe un test de estos, el cambio está mal (Instrucciones § Fixtures).
"""

from __future__ import annotations

import pytest

from validador.hallazgos import AVISO, ERROR
from validador.reglas import validar
from validador.sugerencias import sugerir


def _validar(ruta):
    return validar(ruta.read_text(encoding="utf-8"), ruta.name)


def _codigos(hallazgos, nivel=None):
    return {h.codigo for h in hallazgos if nivel is None or h.nivel == nivel}


# --------------------------------------------------------------------------
# fixtures/diario/ — días válidos: cero errores, avisos sí
# --------------------------------------------------------------------------

DIAS_VALIDOS = [
    "2026-09-14.md",  # día completo, caso base
    "2026-09-15.md",  # el caso que motiva el proyecto
    "2026-09-16.md",  # mínimo viable
    "2026-09-17.md",  # casos límite del parser
    "2026-09-18.md",  # día sin ingestas
]


@pytest.mark.parametrize("nombre", DIAS_VALIDOS)
def test_los_dias_validos_no_dan_ni_un_error(fixtures, nombre):
    errores = [h for h in _validar(fixtures / "diario" / nombre) if h.nivel == ERROR]
    assert errores == [], "\n".join(h.linea_texto() for h in errores)


def test_dia_minimo_es_valido_y_solo_avisa(fixtures):
    """Solo tipo + hora + alimentos. El fixture más importante: así se registra
    un día malo, que es justo cuando más importa no perder el dato."""
    hallazgos = _validar(fixtures / "diario" / "2026-09-16.md")
    assert _codigos(hallazgos, ERROR) == set()
    assert "campos_analisis_ausentes" in _codigos(hallazgos, AVISO)


def test_dia_sin_ingestas_no_tiene_nada_que_decir(fixtures):
    """Un día sin ingestas es un dato, no un problema."""
    assert _validar(fixtures / "diario" / "2026-09-18.md") == []


def test_hambre_no_no_es_el_booleano_de_yaml(fixtures):
    """`hambre_antes: no` sin comillas lo lee PyYAML como False. Es la trampa
    hermana de `hora: 8:15` y el validador no puede caer en ella."""
    hallazgos = _validar(fixtures / "diario" / "2026-09-15.md")
    assert not [h for h in hallazgos if h.codigo == "fuera_de_vocabulario"]


def test_madrugada_y_desorden_no_son_errores(fixtures):
    """00:40 pertenece a este día y las ingestas pueden venir desordenadas:
    ordenarlas es cosa del parser, no del validador."""
    hallazgos = _validar(fixtures / "diario" / "2026-09-17.md")
    assert _codigos(hallazgos, ERROR) == set()


def test_avisos_buscados_del_fixture_de_limites(fixtures):
    """`[otra]` sin texto y `[ninguna, frustracion]`: avisos, nunca errores."""
    avisos = _codigos(_validar(fixtures / "diario" / "2026-09-17.md"), AVISO)
    assert "otra_sin_texto" in avisos
    assert "ninguna_con_otras" in avisos


def test_falta_una_seccion_del_cuerpo_y_no_pasa_nada(fixtures):
    """A 2026-09-17 le falta `## Pensamientos predominantes`."""
    assert "seccion_desconocida" not in _codigos(_validar(fixtures / "diario" / "2026-09-17.md"))


def test_sintomas_vacio_no_es_ambiguo(fixtures):
    """`sintomas: []` significa que no hubo síntomas. Solo las emociones son
    ambiguas al vaciarse, porque tienen `ninguna` para decir justo eso."""
    hallazgos = _validar(fixtures / "diario" / "2026-09-14.md")
    assert "lista_vacia" not in _codigos(hallazgos)


# --------------------------------------------------------------------------
# fixtures/invalidos/ — todos los problemas, en una sola pasada
# --------------------------------------------------------------------------

# (línea, código) de cada fila de la tabla de fixtures/README.md.
ESPERADOS = [
    (2, "fecha_no_coincide"),        # fecha: 2026-09-20 ≠ nombre del fichero
    (3, "tipo_dato"),                # agua_litros: "dos litros"
    (4, "fuera_de_vocabulario"),     # sueno_calidad: Buena
    (6, "fuera_de_vocabulario"),     # tipo: almuerzo
    (7, "hora_sexagesimal"),         # hora: 8:15 sin comillas → 495
    (9, "fuera_de_vocabulario"),     # emociones_antes: [Ansiedad]
    (10, "fuera_de_vocabulario"),    # emociones_despues: [anisedad]
    (11, "fuera_de_vocabulario"),    # energia: cansado
    (12, "fuera_de_vocabulario"),    # sintomas: [hinchazón]
    (13, "fuera_de_vocabulario"),    # lugar: oficina
    (13, "tipo_dato"),               # pantalla: "si"
    (14, "campo_obligatorio_ausente"),  # segunda ingesta sin alimentos
    (15, "hora_invalida"),           # hora: "25:70"
    (19, "lista_vacia"),             # emociones_antes: [] → aviso
]


def test_caza_todos_los_problemas_de_una_pasada(fixtures):
    """Reportar de uno en uno hace inviable corregir un vault de seis meses."""
    hallazgos = _validar(fixtures / "invalidos" / "2026-09-19.md")
    encontrados = {(h.linea, h.codigo) for h in hallazgos}
    faltan = [e for e in ESPERADOS if e not in encontrados]
    assert not faltan, f"no detectados: {faltan}"


def test_la_lista_vacia_es_aviso_y_el_resto_errores(fixtures):
    hallazgos = _validar(fixtures / "invalidos" / "2026-09-19.md")
    por_clave = {(h.linea, h.codigo): h for h in hallazgos}
    assert por_clave[(19, "lista_vacia")].nivel == AVISO
    for linea, codigo in ESPERADOS:
        if codigo != "lista_vacia":
            assert por_clave[(linea, codigo)].nivel == ERROR, f"{linea}:{codigo}"


def test_todo_error_lleva_linea_util(fixtures):
    for h in _validar(fixtures / "invalidos" / "2026-09-19.md"):
        assert h.linea >= 1
        assert h.fichero == "2026-09-19.md"


def test_los_valores_fuera_de_vocabulario_sugieren(fixtures):
    """Sin sugerencia, corregir es fricción, y la fricción mata el registro."""
    hallazgos = _validar(fixtures / "invalidos" / "2026-09-19.md")
    for h in hallazgos:
        if h.codigo == "fuera_de_vocabulario":
            assert h.sugerencia, h.linea_texto()


# --------------------------------------------------------------------------
# Sugerencias — las de la tabla de fixtures/README.md, una a una
# --------------------------------------------------------------------------

@pytest.mark.parametrize("valor,vocabulario,esperado", [
    ("Ansiedad", "emocion", "ansiedad"),      # mayúscula
    ("anisedad", "emocion", "ansiedad"),      # errata
    ("hinchazón", "sintoma", "hinchazon"),    # acento
    ("Buena", "calidad_sueno", "buena"),      # mayúscula
    ("cansado", "energia", "sueno"),          # sinónimo
    ("oficina", "lugar", "trabajo"),          # sinónimo
    ("almuerzo", "tipo_ingesta", "comida"),   # sinónimo
])
def test_sugerencia_esperada(valor, vocabulario, esperado):
    propuesta = sugerir(valor, vocabulario)
    assert esperado in propuesta.candidatos, propuesta


def test_no_se_inventa_una_sugerencia(valor="qwertyuiop"):
    """Ante algo irreconocible se ofrece el vocabulario, no un disparate."""
    propuesta = sugerir(valor, "emocion")
    assert propuesta.motivo == "sin_idea"


# --------------------------------------------------------------------------
# Robustez: el validador no puede romperse, solo reportar
# --------------------------------------------------------------------------

@pytest.mark.parametrize("texto", [
    "",
    "solo texto, sin frontmatter",
    "---\n---\n",
    "---\nfecha: 2026-09-14\ningestas: no-es-una-lista\n---\n",
    "---\nfecha: 2026-09-14\ningestas:\n  - hola\n---\n",
    "---\nfecha: 2026-09-14\n  mal: indentado\n---\n",
    "---\nfecha: 2026-09-14\nfecha: 2026-09-15\n---\n",
    "---\nfecha: 2026-09-14\nemociones: [x]\n---\n",
])
def test_no_revienta_con_basura(texto):
    hallazgos = validar(texto, "2026-09-14.md")
    assert all(h.nivel in (ERROR, AVISO) for h in hallazgos)


def test_clave_duplicada_se_reporta():
    """YAML se queda con la última y pierde la anterior sin decir nada."""
    hallazgos = validar("---\nfecha: 2026-09-14\nfecha: 2026-09-15\n---\n", "2026-09-14.md")
    assert "clave_duplicada" in _codigos(hallazgos, ERROR)


def test_campo_mal_escrito_se_sugiere():
    texto = ('---\nfecha: 2026-09-14\ningestas:\n  - tipo: cena\n    hora: "21:00"\n'
             '    alimentos: sopa\n    emociones_ante: [ninguna]\n---\n')
    hallazgos = validar(texto, "2026-09-14.md")
    desconocidos = [h for h in hallazgos if h.codigo == "campo_desconocido"]
    assert desconocidos and "emociones_antes" in desconocidos[0].sugerencia
