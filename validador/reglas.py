"""Las reglas. Una pasada por nota, todos los hallazgos de golpe.

Regla de oro (fixtures/README.md): no parar en el primer problema. Corregir un
vault de seis meses de uno en uno es inviable, y un validador inviable se deja
de ejecutar.
"""

from __future__ import annotations

import datetime as dt
import re

import yaml

import esquema
from validador import nota as N
from validador.hallazgos import AVISO, ERROR, Hallazgo
from validador.sugerencias import sugerir, sugerir_campo

RE_NOMBRE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.md$")
RE_HORA = re.compile(r"^(\d{1,2}):(\d{2})$")

# Secciones del cuerpo previstas por el esquema. Otras no son un error, pero se
# avisa: un encabezado mal escrito hace que el parser pierda ese texto en silencio.
SECCIONES = ("Reflexiones", "Pensamientos predominantes", "Orgullo y gratitud")

# Lo que necesitan Q1-Q4 de Diseño/Analisis.md. Su ausencia se avisa agrupada, no
# campo a campo: ocho avisos por ingesta serian ruido y el ruido se ignora.
CAMPOS_ANALISIS = ("hambre_antes", "emociones_antes", "emociones_despues", "energia")
CAMPOS_DIA_UTILES = ("sueno_horas", "sueno_calidad", "agua_litros")

# Campo de texto libre que acompaña a cada valor "otra"/"otro"/"otros".
ACOMPANANTES = {
    "emociones_antes": ("otra", "emocion_otra_antes"),
    "emociones_despues": ("otra", "emocion_otra_despues"),
    "sintomas": ("otros", "sintoma_otros"),
}

NUMERICOS = {"tag:yaml.org,2002:int", "tag:yaml.org,2002:float"}

class _Acta:
    """Acumulador de hallazgos de una nota."""

    def __init__(self, fichero: str) -> None:
        self.fichero = fichero
        self.hallazgos: list[Hallazgo] = []

    def error(self, linea: int, codigo: str, mensaje: str, sugerencia: str | None = None) -> None:
        self.hallazgos.append(Hallazgo(ERROR, codigo, linea, mensaje, sugerencia, self.fichero))

    def aviso(self, linea: int, codigo: str, mensaje: str, sugerencia: str | None = None) -> None:
        self.hallazgos.append(Hallazgo(AVISO, codigo, linea, mensaje, sugerencia, self.fichero))


def validar(texto: str, nombre_fichero: str) -> list[Hallazgo]:
    """Valida una nota de diario entera. Devuelve todos sus hallazgos."""
    acta = _Acta(nombre_fichero)

    coincide = RE_NOMBRE.match(nombre_fichero)
    if not coincide:
        acta.error(1, "nombre_fichero",
                   f"el nombre del fichero deberia ser YYYY-MM-DD.md, no {nombre_fichero!r}")

    nota = N.leer(texto, nombre_fichero)

    if nota.sin_frontmatter:
        acta.error(1, "sin_frontmatter",
                   "la nota no tiene frontmatter YAML delimitado por --- al principio y al final")
        return acta.hallazgos

    if nota.error_yaml:
        linea, problema = nota.error_yaml
        acta.error(linea, "yaml_malformado", f"YAML ilegible: {problema}")
        return acta.hallazgos

    raiz = nota.frontmatter
    if raiz is None or N.es_nulo(raiz):
        acta.error(1, "frontmatter_vacio", "el frontmatter esta vacio; falta al menos `fecha`")
        return acta.hallazgos
    if not isinstance(raiz, yaml.MappingNode):
        acta.error(N.linea(raiz), "frontmatter_no_mapa",
                   "el frontmatter deberia ser una lista de campos `clave: valor`")
        return acta.hallazgos

    campos = _revisar_claves(acta, raiz, esquema.campos_dia(), "dia")
    _revisar_dia(acta, campos, coincide.group(1) if coincide else None)
    _revisar_secciones(acta, nota)
    return acta.hallazgos


# --------------------------------------------------------------------------
# Nivel dia
# --------------------------------------------------------------------------

def _revisar_dia(acta: _Acta, campos: dict, fecha_fichero: str | None) -> None:
    for obligatorio in esquema.campos_obligatorios_dia():
        if obligatorio not in campos:
            acta.error(1, "campo_obligatorio_ausente", f"falta el campo `{obligatorio}` del dia")

    if "fecha" in campos:
        _revisar_fecha(acta, campos["fecha"], fecha_fichero)
    _numero(acta, campos.get("agua_litros"), "agua_litros", minimo=0)
    _numero(acta, campos.get("sueno_horas"), "sueno_horas", minimo=0, maximo=24)
    _texto(acta, campos.get("actividad"), "actividad")
    _enum(acta, campos.get("sueno_calidad"), "sueno_calidad", "calidad_sueno")

    ingestas = campos.get("ingestas")
    lista: list[yaml.Node] = []
    if ingestas is not None and not N.es_nulo(ingestas[1]):
        clave, valor_nodo = ingestas
        if not isinstance(valor_nodo, yaml.SequenceNode):
            acta.error(N.linea(clave), "tipo_dato",
                       "`ingestas` deberia ser una lista de ingestas (`- tipo: ...`)")
        else:
            lista = N.elementos(valor_nodo)

    for indice, ingesta in enumerate(lista, start=1):
        _revisar_ingesta(acta, ingesta, indice)

    # Los campos de dia ausentes se avisan juntos y solo si hay algo registrado:
    # un dia entero sin ingestas ya dice lo suyo, no hace falta insistir.
    ausentes = [c for c in CAMPOS_DIA_UTILES if c not in campos]
    if ausentes and lista:
        acta.aviso(1, "campos_dia_ausentes",
                   "el dia no registra " + ", ".join(f"`{c}`" for c in ausentes),
                   "el sueno es el principal factor de confusion de la ansiedad (Diseño/Esquema-de-Datos.md)")


def _revisar_fecha(acta: _Acta, par, fecha_fichero: str | None) -> None:
    clave, valor_nodo = par
    linea = N.linea(clave)
    crudo = N.texto_crudo(valor_nodo).strip()
    valor = N.valor(valor_nodo)

    if not isinstance(valor, (dt.date, str)) or N.es_nulo(valor_nodo):
        acta.error(linea, "tipo_dato", "`fecha` deberia ser una fecha YYYY-MM-DD")
        return
    if isinstance(valor, dt.datetime) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", crudo):
        acta.error(linea, "formato_fecha",
                   f"`fecha: {crudo}` deberia escribirse como YYYY-MM-DD, sin hora")
        return
    if fecha_fichero and crudo != fecha_fichero:
        acta.error(linea, "fecha_no_coincide",
                   f"`fecha: {crudo}` no coincide con el nombre del fichero ({fecha_fichero})",
                   f"manda el nombre del fichero: deberia poner {fecha_fichero}")


# --------------------------------------------------------------------------
# Nivel ingesta
# --------------------------------------------------------------------------

def _revisar_ingesta(acta: _Acta, nodo: yaml.Node, indice: int) -> None:
    linea_ingesta = N.linea(nodo)
    if not isinstance(nodo, yaml.MappingNode):
        acta.error(linea_ingesta, "ingesta_no_mapa",
                   f"la ingesta {indice} no es una lista de campos `clave: valor`")
        return

    campos = _revisar_claves(acta, nodo, esquema.campos_ingesta(), "ingesta")

    for obligatorio in esquema.campos_obligatorios_ingesta():
        if obligatorio not in campos or N.es_nulo(campos[obligatorio][1]):
            acta.error(linea_ingesta, "campo_obligatorio_ausente",
                       f"la ingesta {indice} no registra `{obligatorio}`",
                       "el minimo de una ingesta es tipo + hora + alimentos")

    _enum(acta, campos.get("tipo"), "tipo", "tipo_ingesta")
    _hora(acta, campos.get("hora"), indice)
    _texto(acta, campos.get("alimentos"), "alimentos")
    _enum(acta, campos.get("hambre_antes"), "hambre_antes", "hambre")
    _texto(acta, campos.get("pensamientos_antes"), "pensamientos_antes")
    _texto(acta, campos.get("pensamientos_despues"), "pensamientos_despues")
    _lista_enum(acta, campos.get("emociones_antes"), "emociones_antes", "emocion")
    _lista_enum(acta, campos.get("emociones_despues"), "emociones_despues", "emocion")
    _lista_enum(acta, campos.get("sintomas"), "sintomas", "sintoma")
    _enum(acta, campos.get("energia"), "energia", "energia")
    _revisar_contexto(acta, campos.get("contexto"))
    _revisar_otras(acta, campos)

    ausentes = [c for c in CAMPOS_ANALISIS if c not in campos]
    if ausentes:
        acta.aviso(linea_ingesta, "campos_analisis_ausentes",
                   f"la ingesta {indice} no registra " + ", ".join(f"`{c}`" for c in ausentes),
                   "son los campos que necesitan Q1-Q4; la entrada es valida igualmente")


def _revisar_contexto(acta: _Acta, par) -> None:
    if par is None:
        return
    clave, nodo = par
    if N.es_nulo(nodo):
        acta.aviso(N.linea(clave), "campo_vacio",
                   "`contexto` esta en blanco", "los campos vacios se omiten, no se dejan a medias")
        return
    if not isinstance(nodo, yaml.MappingNode):
        acta.error(N.linea(clave), "tipo_dato",
                   "`contexto` deberia ser `{compania: ..., lugar: ..., pantalla: ...}`")
        return

    campos = _revisar_claves(acta, nodo, esquema.campos_contexto(), "contexto")
    _enum(acta, campos.get("compania"), "compania", "compania")
    _enum(acta, campos.get("lugar"), "lugar", "lugar")

    pantalla = campos.get("pantalla")
    if pantalla and not N.es_nulo(pantalla[1]):
        clave_p, nodo_p = pantalla
        if nodo_p.tag != N.TAG_BOOL:
            crudo = N.texto_crudo(nodo_p)
            acta.error(N.linea(clave_p), "tipo_dato",
                       f"`pantalla: {crudo}` deberia ser `true` o `false`, sin comillas",
                       "true si se comio mirando movil, TV u ordenador")


def _revisar_otras(acta: _Acta, campos: dict) -> None:
    """Coherencia entre un valor `otra`/`otros` y su texto libre."""
    for campo_lista, (marcador, campo_texto) in ACOMPANANTES.items():
        par = campos.get(campo_lista)
        valores = _valores_lista(par)
        tiene_texto = campo_texto in campos and not N.es_nulo(campos[campo_texto][1])
        if marcador in valores and not tiene_texto:
            acta.aviso(N.linea(par[0]), "otra_sin_texto",
                       f"`{campo_lista}` incluye `{marcador}` pero falta `{campo_texto}`",
                       "sin el texto, `otra` no se puede interpretar meses despues")
        if tiene_texto and marcador not in valores:
            acta.aviso(N.linea(campos[campo_texto][0]), "texto_huerfano",
                       f"`{campo_texto}` esta escrito pero `{campo_lista}` no incluye `{marcador}`")

    energia = campos.get("energia")
    valor_energia = N.valor(energia[1]) if energia else None
    tiene_texto = "energia_otro" in campos and not N.es_nulo(campos["energia_otro"][1])
    if valor_energia == "otro" and not tiene_texto:
        acta.aviso(N.linea(energia[0]), "otra_sin_texto",
                   "`energia: otro` pero falta `energia_otro`")
    if tiene_texto and valor_energia != "otro":
        acta.aviso(N.linea(campos["energia_otro"][0]), "texto_huerfano",
                   "`energia_otro` esta escrito pero `energia` no es `otro`")


# --------------------------------------------------------------------------
# Comprobaciones de tipo y vocabulario
# --------------------------------------------------------------------------

def _revisar_claves(acta: _Acta, nodo: yaml.MappingNode, conocidos: tuple[str, ...],
                    ambito: str) -> dict:
    """Detecta claves repetidas y desconocidas. Devuelve {nombre: (clave, valor)}."""
    campos: dict[str, tuple[yaml.ScalarNode, yaml.Node]] = {}
    for clave, valor_nodo in N.pares(nodo):
        nombre = clave.value
        if nombre in campos:
            acta.error(N.linea(clave), "clave_duplicada",
                       f"`{nombre}` aparece dos veces en el mismo {ambito}",
                       "YAML se queda solo con la ultima; la anterior se pierde sin avisar")
            campos[nombre] = (clave, valor_nodo)
            continue
        if nombre not in conocidos:
            propuesta = sugerir_campo(nombre, conocidos)
            acta.error(N.linea(clave), "campo_desconocido",
                       f"`{nombre}` no es un campo de {ambito}",
                       propuesta.texto() if propuesta else None)
            continue
        campos[nombre] = (clave, valor_nodo)
    return campos


def _enum(acta: _Acta, par, campo: str, vocabulario: str) -> None:
    if par is None:
        return
    clave, nodo = par
    if N.es_nulo(nodo):
        acta.aviso(N.linea(clave), "campo_vacio", f"`{campo}` esta en blanco",
                   "los campos vacios se omiten, no se dejan escritos en blanco")
        return
    if not N.es_escalar(nodo):
        acta.error(N.linea(clave), "tipo_dato", f"`{campo}` deberia ser un unico valor")
        return
    valor = esquema.destrampar(N.valor(nodo), vocabulario)
    if isinstance(valor, str) and valor in esquema.vocabularios()[vocabulario]:
        return
    crudo = N.texto_crudo(nodo)
    propuesta = sugerir(valor if isinstance(valor, str) else crudo, vocabulario)
    acta.error(N.linea(clave), "fuera_de_vocabulario",
               f"`{campo}: {crudo}` no esta en el vocabulario `{vocabulario}`",
               propuesta.texto() if propuesta else None)


def _lista_enum(acta: _Acta, par, campo: str, vocabulario: str) -> None:
    if par is None:
        return
    clave, nodo = par
    if N.es_nulo(nodo):
        acta.aviso(N.linea(clave), "campo_vacio", f"`{campo}` esta en blanco",
                   "los campos vacios se omiten; si no hubo nada, `[ninguna]`")
        return
    if not isinstance(nodo, yaml.SequenceNode):
        acta.error(N.linea(clave), "tipo_dato",
                   f"`{campo}` deberia ser una lista entre corchetes, p.ej. `[ansiedad]`")
        return

    neutro = "ninguna" if vocabulario == "emocion" else None

    elementos = N.elementos(nodo)
    if not elementos:
        # `sintomas: []` no es ambiguo: significa que no hubo sintomas. `emociones: []`
        # si lo es, porque el vocabulario tiene `ninguna` para decir justo eso: o se
        # quiso decir `[ninguna]`, o no se anoto nada. Son dos datos distintos.
        if neutro:
            acta.aviso(N.linea(clave), "lista_vacia",
                       f"`{campo}` es una lista vacia",
                       f"ambiguo: si no hubo nada, `[{neutro}]`; si no se anoto, se omite la linea")
        return

    valores: list[str] = []
    for elemento in elementos:
        if not N.es_escalar(elemento):
            acta.error(N.linea(elemento), "tipo_dato", f"un elemento de `{campo}` no es un valor")
            continue
        valor = esquema.destrampar(N.valor(elemento), vocabulario)
        if isinstance(valor, str) and valor in esquema.vocabularios()[vocabulario]:
            valores.append(valor)
            continue
        crudo = N.texto_crudo(elemento)
        propuesta = sugerir(valor if isinstance(valor, str) else crudo, vocabulario)
        acta.error(N.linea(elemento), "fuera_de_vocabulario",
                   f"`{crudo}` no esta en el vocabulario `{vocabulario}` (campo `{campo}`)",
                   propuesta.texto() if propuesta else None)

    if len(valores) != len(set(valores)):
        repetidos = sorted({v for v in valores if valores.count(v) > 1})
        acta.aviso(N.linea(clave), "valor_repetido",
                   f"`{campo}` repite " + ", ".join(f"`{v}`" for v in repetidos))

    if neutro and neutro in valores and len(set(valores)) > 1:
        acta.aviso(N.linea(clave), "ninguna_con_otras",
                   f"`{campo}` mezcla `{neutro}` con otras emociones",
                   "o no habia nada, o habia algo: elegir una de las dos lecturas")


def _numero(acta: _Acta, par, campo: str, minimo=None, maximo=None) -> None:
    if par is None:
        return
    clave, nodo = par
    if N.es_nulo(nodo):
        acta.aviso(N.linea(clave), "campo_vacio", f"`{campo}` esta en blanco",
                   "los campos vacios se omiten, no se dejan escritos en blanco")
        return
    if not N.es_escalar(nodo) or nodo.tag not in NUMERICOS:
        crudo = N.texto_crudo(nodo)
        acta.error(N.linea(clave), "tipo_dato",
                   f"`{campo}: {crudo}` deberia ser un numero",
                   "sin comillas y con punto decimal, p.ej. `1.8`")
        return
    valor = N.valor(nodo)
    if minimo is not None and valor < minimo:
        acta.error(N.linea(clave), "fuera_de_rango", f"`{campo}: {valor}` no puede ser menor que {minimo}")
    if maximo is not None and valor > maximo:
        acta.error(N.linea(clave), "fuera_de_rango", f"`{campo}: {valor}` no puede ser mayor que {maximo}")


def _texto(acta: _Acta, par, campo: str) -> None:
    if par is None:
        return
    clave, nodo = par
    if N.es_nulo(nodo):
        acta.aviso(N.linea(clave), "campo_vacio", f"`{campo}` esta en blanco",
                   "los campos vacios se omiten, no se dejan escritos en blanco")
        return
    if not N.es_escalar(nodo):
        acta.error(N.linea(clave), "tipo_dato", f"`{campo}` deberia ser texto")
        return
    if not str(N.valor(nodo)).strip():
        acta.aviso(N.linea(clave), "campo_vacio", f"`{campo}` esta vacio")


def _hora(acta: _Acta, par, indice: int) -> None:
    if par is None:
        return
    clave, nodo = par
    linea = N.linea(clave)
    if N.es_nulo(nodo):
        return  # ya lo reporta la comprobacion de campos obligatorios
    crudo = N.texto_crudo(nodo)

    # El error mas traicionero del formato: sin comillas, YAML 1.1 lee 8:15 como
    # sexagesimal y lo guarda como 495. No falla; corrompe.
    if nodo.tag == N.TAG_INT and ":" in crudo:
        acta.error(linea, "hora_sexagesimal",
                   f"`hora: {crudo}` sin comillas: YAML la convierte en el numero {N.valor(nodo)}",
                   f'escribir `hora: "{crudo}"` entre comillas')
        return
    if nodo.tag != N.TAG_STR:
        acta.error(linea, "tipo_dato", f'`hora: {crudo}` deberia ser texto entre comillas, "HH:MM"')
        return

    coincide = RE_HORA.match(crudo.strip())
    if not coincide:
        acta.error(linea, "formato_hora", f'`hora: "{crudo}"` deberia tener el formato "HH:MM"')
        return
    horas, minutos = int(coincide.group(1)), int(coincide.group(2))
    if horas > 23 or minutos > 59:
        acta.error(linea, "hora_invalida", f'`hora: "{crudo}"` no existe')
        return
    if len(coincide.group(1)) == 1:
        acta.aviso(linea, "hora_sin_cero", f'`hora: "{crudo}"` deberia llevar cero delante',
                   f'escribir `"{horas:02d}:{minutos:02d}"` para que ordene bien')


def _valores_lista(par) -> list[str]:
    if par is None or not isinstance(par[1], yaml.SequenceNode):
        return []
    return [N.valor(e) for e in N.elementos(par[1]) if N.es_escalar(e)]


# --------------------------------------------------------------------------
# Cuerpo de la nota
# --------------------------------------------------------------------------

def _revisar_secciones(acta: _Acta, nota: N.Nota) -> None:
    """Una seccion ausente no es nada. Una mal escrita pierde el texto en silencio."""
    conocidas = {esquema.normalizar(s): s for s in SECCIONES}
    for titulo in nota.secciones:
        if esquema.normalizar(titulo) in conocidas:
            continue
        propuesta = sugerir_campo(titulo, tuple(conocidas))
        cercana = propuesta.candidatos[0] if propuesta and propuesta.motivo != "sin_idea" else None
        acta.aviso(1, "seccion_desconocida",
                   f"la seccion `## {titulo}` no es una de las previstas",
                   f"quiza `## {conocidas[cercana]}`" if cercana else
                   "previstas: " + ", ".join(f"`## {s}`" for s in SECCIONES))
