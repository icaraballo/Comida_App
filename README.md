# Comida App — código

Registro de alimentación y estado emocional. Local, usuario único, sin nube.

**La documentación vive en el vault**, no aquí: `../Vault Proyectos/Comida_App/`.
Empezar por su `Índice.md`. Este repo es sólo la implementación.

| En el vault | Qué es |
|---|---|
| `Tareas/Instrucciones.md` | Principios no negociables y la lista de qué **no** construir |
| `Tareas/Fase-0-Obsidian.md` | Cómo registrar hoy, sin código |
| `Diseño/Esquema-de-Datos.md` | **El contrato de datos.** Manda sobre el código |
| `Diseño/Decisiones.md` | Las nueve decisiones (D1–D9), con su motivo |
| `Diseño/Analisis.md` | Las cuatro preguntas pre-registradas (Q1–Q4) |
| `Diseño/Banco-de-Ideas.md` | Decisiones abiertas e ideas |
| `QA/` | Bugs activos, sin verificar, resueltos y compatibilidad |
| `fixtures/` | Contrato de aceptación del parser y del validador |

## Estado

| Punto | Qué | Estado |
|---|---|---|
| 1 | `esquema/` — JSON Schema + vocabularios cerrados | ✅ v1 |
| 2 | `parser/` — dataframe *tidy*, parquet y SQLite | ✅ v1 |
| 3 | `validar.py` — erratas, vocabulario y campos ausentes | ✅ v1 |
| — | `visor/` — página local de revisión (calendario + día) | ✅ v1 |
| 4 | Captura rápida (PWA móvil) | 🔒 después de la Fase 0 |
| 5 | Calendario de revisión interactivo | 🔒 después de la Fase 0 |
| 6 | Vistas de análisis (Q1–Q4) | 🔒 después de 4–6 semanas de registro |

Los puntos 1–3 no necesitan datos reales, por eso están hechos. Del 4 en adelante
**no se construye a ciegas**: su entrada son las cuatro preguntas del final de
`Tareas/Fase-0-Obsidian.md`, y para responderlas hay que haber registrado.

## Uso

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# 1. ¿Está bien escrito el vault?
.venv/bin/python validar.py <ruta-del-diario>
.venv/bin/python validar.py <ruta> --solo-errores   # sin avisos
.venv/bin/python validar.py <ruta> --json           # para otras herramientas
.venv/bin/python validar.py <ruta> --schema         # cruza con el JSON Schema

# 2. Generar la capa derivada (parquet + SQLite, para pandas o Power BI)
.venv/bin/python parsear.py <ruta-del-diario>
.venv/bin/python parsear.py <ruta> --resumen        # no escribe nada

# 3. Verlo
.venv/bin/python ver.py <ruta-del-diario>           # genera y abre el visor
```

`validar.py` sale con código 1 si hay **errores**. Los avisos nunca hacen fallar
nada: avisar de un campo ausente no es rechazar la entrada (principio 3 de
`Tareas/Instrucciones.md`). Salida en formato de compilador, `fichero:línea:`,
que VS Code hace clicable:

```
2026-09-19.md:7: ERROR [hora_sexagesimal] `hora: 8:15` sin comillas: YAML la
  convierte en el numero 495 — escribir `hora: "8:15"` entre comillas
2026-09-19.md:11: ERROR [fuera_de_vocabulario] `energia: cansado` no esta en el
  vocabulario `energia` — quiza `sueno` o `baja`
```

## El visor

`ver.py` genera `derivado/visor.html`: **un único fichero local y autocontenido**,
sin CDN, sin fuentes remotas y sin una sola petición de red. Son datos de estado
emocional y pensamientos: la superficie de exposición es cero por defecto (D9).
Hay un test que lo comprueba en cada ejecución.

Enseña **calendario y día**, y ni un gráfico de patrones. No es una limitación
técnica: `Diseño/Analisis.md` pide 4–6 semanas de registro antes de mirar nada.
Y los días se colorean sólo por *si hay registro*, nunca por cómo fue el día —
un semáforo de "buen día / mal día" está expresamente prohibido en las
instrucciones del proyecto.

## Qué hay dentro

```
esquema/
  dia.schema.json    el contrato: campos, tipos y vocabularios cerrados
  sinonimos.json     ayuda para corregir ('oficina' → 'trabajo'). No es contrato
  __init__.py        carga ambos; única fuente de los enums en código
validador/
  nota.py            trocea la nota y conserva el número de línea
  reglas.py          las reglas; una pasada, todos los hallazgos
  sugerencias.py     ortografía → sinónimo → errata → rendirse con elegancia
  contraste.py       segunda pasada contra el JSON Schema (--schema)
  hallazgos.py       ERROR / AVISO
parser/
  lector.py          .md → diccionario, deshaciendo las trampas de YAML
  tidy.py            una fila por ingesta + tabla de días, con los derivados
  exportar.py        parquet, SQLite y la tabla larga de emociones
visor/
  datos.py           de la capa derivada a lo que consume la página
  plantilla.py       la página: HTML, CSS y JS en un fichero
  generar.py         escribe el visor
validar.py  parsear.py  ver.py     las tres CLIs
tests/                             contrato de aceptación (59 tests)
```

Ningún enum está escrito a mano en el código: `esquema/__init__.py` los lee de
`dia.schema.json`, y hasta el mapa campo→vocabulario se deriva de sus `$ref`.
Para añadir un valor al vocabulario se toca `Diseño/Esquema-de-Datos.md` (el
vault) y luego `dia.schema.json`, **en ese orden**.

## Tests

```bash
.venv/bin/python -m pytest tests -q
```

Los fixtures **no se copian aquí**: son el contrato de aceptación y viven junto a
la documentación que los explica, en el vault. Los tests los buscan al lado
(`../Vault Proyectos/Comida_App/fixtures`) y se saltan solos si no están. Para
apuntar a otro sitio:

```bash
COMIDA_FIXTURES=/ruta/a/fixtures .venv/bin/python -m pytest tests -q
```

## Las dos trampas de YAML 1.1

Las dos corrompen en silencio, sin dar error, y las dos están cubiertas:

- `hora: 8:15` sin comillas se lee como el **entero 495** (sexagesimal). El
  validador lo caza y pide comillas.
- `hambre_antes: no` sin comillas se lee como el **booleano `False`** (la lista
  de PyYAML incluye `yes`/`no`/`on`/`off`), y `no` es un valor del vocabulario
  `hambre`. Se deshace en `esquema.destrampar()`, en un único sitio.
  **Decisión abierta**, ver `Diseño/Banco-de-Ideas.md` §1.1.

## Privacidad

Aquí no entra ni un dato real: `diario/` y `derivado/` están en `.gitignore`.
El registro vive en el vault de Obsidian. Repositorio privado (D9).
