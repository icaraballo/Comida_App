# Comida App — contexto para Claude Code

**La documentación canónica vive en el vault**, no aquí:
`../Vault Proyectos/Comida_App/`. Empezar por su `Índice.md`.

Este fichero no duplica nada: sólo recuerda las reglas que no se pueden
descubrir leyendo el código, y dice dónde está lo demás. Si algo de aquí choca
con `Tareas/Instrucciones.md` del vault, **manda el vault**.

## Las cinco reglas que no se deducen del código

1. **El markdown es la fuente de verdad.** Parquet y SQLite son capa derivada y
   regenerable. Nunca se escribe en la base de datos (D1).
2. **Registrar tiene que costar menos de 20 segundos.** El proyecto no fracasa
   por bugs, fracasa por abandono del registro. Cualquier campo obligatorio
   nuevo es una amenaza directa.
3. **Una entrada con sólo `tipo` + `hora` + `alimentos` es válida.** El validador
   avisa de lo ausente, nunca rechaza.
4. **Captura y clasificación van separadas.** Los alimentos se registran en texto
   libre; el etiquetado es posterior y en batch.
5. **El orden de construcción importa**: esquema → parser → validador → captura →
   calendario → análisis. No empezar por la captura aunque sea lo más vistoso.

## Qué NO construir

Calorías, macros, peso, IMC, objetivos, puntuaciones del día, semáforos de
"buen día / mal día", clasificar alimentos en saludable/no saludable, rachas,
gamificación, notificaciones que presionen a registrar, nube, telemetría.

La plantilla en papel no tiene nada de esto y **esa ausencia es deliberada**: es
un registro de conciencia, no de control. Si se pide algo de esta lista, señalar
`Tareas/Instrucciones.md` del vault y pedir confirmación explícita.

## Antes de tocar el esquema

Se actualiza primero `Diseño/Esquema-de-Datos.md` en el vault, después
`esquema/dia.schema.json`. En ese orden. Los enums no se escriben a mano en
ningún otro sitio: se leen del schema.

## Fixtures

Contrato de aceptación, en el vault (`fixtures/`). Si un cambio rompe un fixture,
el cambio está mal. `fixtures/README.md` explica qué prueba cada uno.

## Notas de trabajo

- Idioma del código, los datos y la conversación: **castellano**. Los valores de
  enum van en minúsculas y sin acentos.
- Un bug que añade fricción al registrar es crítico aunque sea una tontería
  técnica. Ficha en `QA/Bugs-Activos.md` del vault.
- El usuario trabaja en VS Code sobre macOS. Homebrew Python es *externally
  managed*: usar `.venv`.
