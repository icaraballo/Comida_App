# Comida App — contexto para Claude Code

**La documentación canónica vive en el vault**, no aquí:
`../Vault Proyectos/Comida_App/`. Empezar por `Comida App.md`, y para la app
de registro, por `Tareas/CA-Especificacion-App-Registro.md`.

Este fichero no duplica nada: sólo recuerda las reglas que no se pueden
descubrir leyendo el código, y dice dónde está lo demás. Si algo de aquí choca
con `Tareas/CA-Instrucciones.md` del vault, **manda el vault**.

## Las cinco reglas que no se deducen del código

1. **La fuente de verdad es la app, en el dispositivo** (D1 revisada). El
   markdown es un formato de exportación, y tiene que seguir el esquema para
   que `validar.py` y `parsear.py` funcionen sobre él. Sin cuentas: cada móvil
   es una persona (D12).
2. **Registrar tiene que costar menos de 20 segundos.** El proyecto no fracasa
   por bugs, fracasa por abandono del registro. Cualquier campo obligatorio
   nuevo es una amenaza directa.
3. **Una entrada con sólo `tipo` + `hora` + `alimentos` es válida.** El validador
   avisa de lo ausente, nunca rechaza.
4. **Captura y clasificación van separadas.** Los alimentos se registran en texto
   libre; el etiquetado es posterior y en batch.
5. **El prototipo manda sobre el aspecto.** `app/` parte de
   `CA-Prototipo-v0.4.html` (vault, `Tareas/`) y tiene que verse y comportarse
   igual. Si la especificación y el prototipo discrepan, preguntar. Los puntos
   abiertos de su §11 no se deciden sin el usuario.

## Qué NO construir

Calorías, macros, peso, IMC, objetivos, puntuaciones del día, semáforos de
"buen día / mal día", clasificar alimentos en saludable/no saludable, rachas,
gamificación, notificaciones que presionen a registrar, nube, telemetría.

La plantilla en papel no tiene nada de esto y **esa ausencia es deliberada**: es
un registro de conciencia, no de control. Si se pide algo de esta lista, señalar
`Tareas/CA-Instrucciones.md` del vault y pedir confirmación explícita.

## Antes de tocar el esquema

Se actualiza primero `Diseño/CA-Esquema-de-Datos.md` en el vault, después
`esquema/dia.schema.json`. En ese orden. Los enums no se escriben a mano en
ningún otro sitio: se leen del schema. Tampoco en el JS de `app/`.

## Fixtures

Contrato de aceptación, en el vault (`fixtures/`). Si un cambio rompe un fixture,
el cambio está mal. `fixtures/CA-Fixtures.md` explica qué prueba cada uno.

## Notas de trabajo

- Idioma del código, los datos y la conversación: **castellano**. Los valores de
  enum van en minúsculas y sin acentos.
- Un bug que añade fricción al registrar es crítico aunque sea una tontería
  técnica. Ficha en `QA/CA-Bugs-Activos.md` del vault.
- El usuario trabaja en VS Code sobre macOS. Homebrew Python es *externally
  managed*: usar `.venv`.
