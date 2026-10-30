# Inventario de validación H0–H3

Fecha de corte: 2026-10-29. Este documento resume la evidencia declarada en las fichas de hito y registros enlazados; no convierte los conteos de candidatos en funciones aceptadas. Las pruebas aceptan contratos y dominios delimitados.

## Resumen por hito

| Hito | Recorrido o resultado observado | C++ integrado o promovido | Dependencias/límites que impiden una afirmación más amplia |
| --- | --- | --- | --- |
| H0 — Base | El batch 4 arrancó en Azahar, llegó al título y recorrió título → Audio Settings → título. Se observaron entradas en `0x0037C46C` y `0x002ADB40`. | H0 valida el método de prueba y los dos hits; no reconstruye por sí mismo la lógica completa del menú. | Los hits sólo demuestran llegada a entradas. La ficha no valida todo el menú ni una partida. Reproducibilidad actual de los artefactos y entorno debe verificarse en el cierre H0–H3. |
| H1 — Menú | Navegación y wraparound `0..3`, textos de ayuda, acceso a Audio Settings, vuelta al menú y despacho de las opciones cubiertas se compararon en simulador ARM y Azahar. | `Tbb_GetSubTable` (`0x002AC2F4`), `Tbb_GetPayloadData` (`0x002C0E9C`), `Tbb_GetDefaultTable18Payload` (`0x002C0E84`); `H1_TitleMain_UpdateNavigationSlice` (`0x001E9D08..0x001E9DDC`) y `H1_TitleMain_ProcessConfirmationSlice` (`0x001EA160..0x001EA328`). Helpers TBB y ambas rebanadas están integrados según su ficha. | Inicialización y callbacks de presentación/dibujo tienen límites explícitos; los despachos prueban el inicio de destinos, no la lógica interna de cada destino. La ficha enumera rutas AOC y otras ramas pendientes. |
| H2 — Audio | Abierto. La corrida RSP corregida anterior conserva 12 checkpoints y 29 acciones lógicas emparejadas. El sondeo ampliado ejercitó los extremos en el lado original y llegó a A-confirm/State 2. Run 003 reportó 40 polls con `r0=0`, pero su log preserva 39 respuestas completas; run 005 preserva 40 respuestas cero. No hubo retorno, cierre limpio ni prueba de reinicio. | En producción: mappers `0x002CAB70`, `0x0021F39C`, `0x002E0AF4`; `UiConfig_FillPair` (`0x0027EDF8`); `UiConfig_CopyPair` (`0x002ADB40`); inicializador `0x002F4CA0`; Calc, Draw, Secondary y ready gate están presentes en una imagen reproducible según la ficha. `UiTouch_GetRegionTouchState` (`0x0029D8FC`) y `script_vm_func_0019DFBC` tienen C++ tipado en producción, pero no están en la imagen IPS H2 final descrita. | El sondeo nuevo no logró una comparación runtime parcheada para los límites ni persistencia. El reporte diferencial offline del artefacto integrado pasa los casos contados, pero señala cuatro discrepancias de identidad entre fuentes del checkout y sus hashes de manifiesto. Allocator, factories, recursos, cursor, cargas asíncronas, sonido y otros servicios permanecen originales o modelados como HLE. Véase [el resultado parcial del sondeo](agent-work/h2-rsp-slider-boundaries-restart.md). |
| H3 — Carga | En la composición final, el guardado conocido obtuvo acuse, llegó al field manager y completó 250 callbacks concordantes. Ranura vacía y cancelación están respaldadas por ejecuciones emparejadas previas. Una prueba separada truncó la copia después de abrir: `AsdSave_Read r0=0`; el control intacto dio `r0=1`. No se capturó respuesta final del error. | `SaveLoad_BeginFromTitle` (`0x0030A9A4`) tiene candidato compilado, caller composition y runtime integrado para la ruta feliz delimitada. | Reader/parser/I/O y validación siguen originales. El fallo de apertura se distingue del fallo de lectura real. Para este último, el validador devuelve `r0=1`, sin acuse, entrada al field manager ni mensaje visible capturados. La fuente del usuario conservó su hash; los nueve hashes del paquete de composición fueron verificados independientemente. |

## Funciones nombradas en la evidencia H2

Esta lista identifica el conjunto de funciones H2 descrito explícitamente por la ficha; los estados son los que la documentación declara y requieren reconciliación cuando se contradicen.

| Dirección | Nombre/función | Estado de fuente y evidencia registrada |
| --- | --- | --- |
| `0x002F4CA0` | `titleConfig_func_002f4ca0` | C++ de producción; 10/10 casos finales y caller State-9/10 3/3. Varios servicios del inicializador son dependencias originales/HLE. |
| `0x001EA928` | `TitleConfig_Calc` | Presente en imagen integrada; secuencias de callback y regresión combinada descritas en H2. Scheduler y servicios reales de entrada no quedan probados por la composición aislada. |
| `0x002CAFD0` | `TitleConfig_Draw` | Presente en imagen integrada; diferencial del callback; compositor/render real y servicios dependen de límites indicados en H2. |
| `0x002CAEF0` | `TitleConfig_Secondary` | Presente en imagen integrada; callback probado en matriz bajo el modelo del runner. |
| `0x002FC0EC` | `TitleConfig_IsReady` | Compuerta integrada; caller State-9/10 3/3 bajo el fixture del runner. |
| `0x002CAB70`, `0x0021F39C`, `0x002E0AF4` | Mappers de configuración A/B/C | C++ de producción e imagen extendida reproducible; 512/512 por helper en cada una de dos semillas; revisión independiente registrada para el dominio u8 observado. |
| `0x0027EDF8` | `UiConfig_FillPair` | C++ de producción; 4.096 casos y revisión independiente; ledger `non_matching`. |
| `0x002ADB40` | `UiConfig_CopyPair` | Interfaz C++ tipada; 545/545 casos y revisión independiente; compilado igual al cuerpo original en el alcance registrado; ledger `matching`. |
| `0x0029D8FC` | `UiTouch_GetRegionTouchState` | C++ tipado en producción; 589.824 combinaciones y 45 casos dirigidos; el cuerpo excede el span original y no está en el IPS H2 descrito. Semántica del byte/cadencia runtime abierta. |
| `0x0019DFBC` | `script_vm_func_0019dfbc` | C++ tipado en producción; cinco secuencias con handlers sintéticos; cuerpo `non_matching` y aún no integrado en la imagen IPS H2 descrita. Handlers reales sin resolver. |
| `0x002BFFBC`, `0x002B902C` | Queries lógicas mode-1 y mode-0 | C++ tipado y diferenciales revisados; mode-1: 506 llamadas; mode-0: 140.884 casos. La composición alcanza IDs solicitados, pero no prueba productor/cadencia de input. No aparecen como reemplazos integrados en la imagen descrita. |

## Funciones nombradas en H0, H1 y H3

- **H0:** los reemplazos observados fueron `state_flags` en `0x0037C46C` y `two_word_copy` en `0x002ADB40`. H0 es infraestructura de recorrido y aplicación del parche, no una afirmación funcional sobre todas las entradas.
- **H1:** entrada `titleMain_func_001EB02C`; callback `ui_func_001E989C`; `Title_ResetForBoot` (`0x001EA3D8`); helpers TBB anteriores; las dos rebanadas C++ integradas de navegación y confirmación. El resto del callback mantiene ramas, dependencias y callbacks originales según la ficha.
- **H3:** `SaveLoad_BeginFromTitle` (`0x0030A9A4`) implementa el setup/handoff. El proceso de slot y lectura, incluidos `0x002D8E60`, `0x002EF9AC`, el parser y la E/S, siguen siendo funciones originales en este alcance.

## Trabajo de inventario pendiente

1. Verificar cada fila contra el ledger (`config/functions.csv`), fuente de producción, límites de función y registros por dirección.
2. Enlazar por dirección cada reporte diferencial, composición, revisión y runtime; distinguir `passed` de un archivo de test que sólo contiene aserciones.
3. La cabecera H2 y este resumen reflejan ahora el estado abierto y el sondeo parcial de 2026-10-29; falta contrastar cada criterio individual con su evidencia antes de cerrar el hito.
4. Para H1, completar la lista de dependencias que participan realmente en cada recorrido aceptado; separar pruebas del cuerpo completo, rebanadas y stubs/HLE.
5. Para H3, separar el fallo de apertura del retorno real `AsdSave_Read r0=0` tras abrir. No atribuir al fallo de lectura el marcador de estado 7 observado en el caso de apertura; su respuesta posterior sigue limitada y bajo revisión.
6. Publicar después un conteo por estado sustentado por esta matriz; no usar el total de 180 definiciones experimentales como número de funciones aceptadas.

Fuentes: [plan de validación H0–H3](plan-validacion-h0-h3.md), [estado funcional](functional-status.md), [plan de hitos](reconstruction-milestones.md), y fichas [H0](milestones/H0-reproducible-test-base.md), [H1](milestones/H1-main-menu-flow.md), [H2](milestones/H2-audio-settings.md), [H3](milestones/H3-load-from-title.md).
