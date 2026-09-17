# Comida App — código

Registro de alimentación y estado emocional. Local, usuario único, sin nube.

**La documentación vive en el vault**, no aquí: `../Vault Proyectos/Comida_App/`
(`CLAUDE.md`, `docs/esquema.md`, `docs/decisiones.md`, `docs/analisis.md`,
`docs/fase-0-obsidian.md` y `fixtures/`). Este repo es solo la implementación.

## Estado

Del orden de construcción (esquema → parser → validador → captura → calendario →
análisis) están hechos el **1** y el **3**:

| Punto | Qué | Estado |
|---|---|---|
| 1 | `esquema/` — JSON Schema + vocabularios cerrados | ✅ |
| 2 | `parser/` — dataframe *tidy*, parquet y SQLite | pendiente |
| 3 | `validar.py` — erratas, vocabulario y campos ausentes | ✅ |
| 4 | Captura rápida (PWA móvil) | pendiente |
| 5 | Calendario de revisión | pendiente |
| 6 | Vistas de análisis | pendiente |

## Uso

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

.venv/bin/python validar.py ruta/al/vault/diario      # una carpeta o un .md
.venv/bin/python validar.py <ruta> --solo-errores     # sin avisos
.venv/bin/python validar.py <ruta> --json             # para otras herramientas
.venv/bin/python validar.py <ruta> --schema           # cruza con el JSON Schema
```

Sale con código 1 si hay **errores**. Los avisos nunca hacen fallar nada: avisar
de un campo ausente no es rechazar la entrada (principio 3 de `CLAUDE.md`).

Salida en formato de compilador, `fichero:línea:`, que VS Code hace clicable:

```
2026-09-19.md:7: ERROR [hora_sexagesimal] `hora: 8:15` sin comillas: YAML la
  convierte en el numero 495 — escribir `hora: "8:15"` entre comillas
2026-09-19.md:11: ERROR [fuera_de_vocabulario] `energia: cansado` no esta en el
  vocabulario `energia` — quiza `sueno` o `baja`
```

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
validar.py           la CLI
tests/               contrato de aceptación sobre los fixtures del vault
```

Ningún enum está escrito a mano en el código: `esquema/__init__.py` los lee de
`dia.schema.json`, y hasta el mapa campo→vocabulario se deriva de sus `$ref`.
Para añadir un valor al vocabulario se toca `docs/esquema.md` (el vault) y luego
`dia.schema.json`, en ese orden.

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
  `hambre`. Se acepta y se deshace en `esquema.destrampar()`, en un único sitio.
  **Decisión pendiente**: dejarlo así o exigir comillas en `docs/esquema.md`.

## Privacidad

Aquí no entra ni un dato real: `diario/` y `derivado/` están en `.gitignore`.
El registro vive en el vault de Obsidian. Repositorio privado (D9).
