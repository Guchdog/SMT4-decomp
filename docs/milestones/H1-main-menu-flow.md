# H1 — Menú principal

Estado: familias parciales verificadas en ARM; falta la transición visual completa, integrar el callback y validar entradas/runtime en Azahar
Responsable de integración: agente principal
Revisión base y fecha: `codex/semantic-equivalence-experiment`, 2026-10-24

## Resultado esperado

Desde un arranque reproducible, inicializar el menú principal, mover la
selección, confirmar cada entrada no destructiva y llegar a su destino previsto.
El alcance de H1 termina en el despacho y la transición inicial; la lógica de
Audio Settings, la selección de partidas y los destinos posteriores se cubren en
otros hitos.

## Alcance y exclusiones

Incluye la inicialización y el ciclo de estados del título, selección por
entrada, actualización de la opción resaltada, confirmación, acceso seguro a
Audio Settings y retorno al título. Se documentan las otras rutas sin
ejecutarlas todavía.

No incluye iniciar una partida nueva, elegir/cargar/guardar una partida ni
seguir la ruta de Add-On Content. No cambiar opciones durante las pruebas H1.
Esas rutas pueden crear estado persistente o depender de contenido aún no
entendido.

## Mapa estático del flujo

La entrada principal identificada es `titleMain_func_001eb02c` (`0x001EB02C`),
que reserva un área de trabajo de `0xA0` bytes en `0x0044E300` y registra
`ui_func_001e989c` (`0x001E989C`) como callback de cálculo. El callback contiene
una tabla de 13 estados en `0x001E98C4`; el estado 5, desde `0x001E9D08`, procesa
el menú. No se ha localizado en el árbol de fuentes un llamador de la
inicialización; el estado inicial `0x9C=0` sí se deduce de la limpieza del
bloque de trabajo en la ruta del allocator, detallada abajo.

| Estado | Comportamiento observado en el listado ARM | Resultado/espera |
| --- | --- | --- |
| 0–1 | Carga el slot TBB `0x3A` y espera animación inicial | Sigue a la preparación del título |
| 2–3 | Solicita recursos del título y espera su carga | Sigue a la preparación de cámara/modelos |
| 4 | Prepara cámara/modelos del título | Sigue al menú |
| 5 | Actualiza selección, texto de ayuda y confirma opción | Despacha a estados 6, 7, 9 u 11 |
| 6, 12 | Salida de título / transición de Nueva partida | Llega a `Script_StartNewGame` (`0x0026FA94`) |
| 7–8 | Prepara y espera el flujo de carga | `SaveLoad_BeginFromTitle` (`0x0030A9A4`) |
| 9–10 | Abre y espera configuración de título | `titleConfig_func_002f4ca0` (`0x002F4CA0`); al terminar espera `0x002FC0EC` y reinicia el título |
| 11–12 | Solicita evento de Add-On Content y espera salida | El destino posterior sigue sin determinar |

`Title_ResetForBoot` (`0x001EA3D8`) limpia regiones táctiles, recursos y flags,
y devuelve el ciclo al estado 5. La selección tiene cuatro índices, con orden
visible confirmado en pantalla: 0 Nueva partida, 1 Cargar partida, 2 Audio
Settings y 3 Add-On Content. La inicialización deja seleccionado el índice 1.

En el estado 5, IDs de trigger `5`/`0xE` decrementan e `6`/`0xF` incrementan el
índice con wraparound entre 0 y 3. Al cambiar la selección se solicita el evento
`0x0100016C`. Las cuatro regiones táctiles pueden cambiar la selección; los
estados táctiles 1/2 mueven el cursor y el estado 6 marca confirmación. La
confirmación también puede proceder de `UiInput_Trigger2(0)`. Los IDs son
índices lógicos; el mapeo a botones físicos no está establecido por el listado
y se medirá de forma controlada antes de fijar pruebas de navegación.

La etiqueta de ayuda seleccionada se lee del slot TBB `0x3A`, en el payload con
stride `0x56` y desplazamiento `0x16`. Las dependencias identificadas incluyen
`Tbb_EnsureSlotLoaded` (`0x002976AC`), `Title_LoadLayout` (`0x002A61F8`),
`Camp_SetSlotMessage` (`0x0029F10C`) y rutinas de dibujo de texto/sprite.

Los IDs `5`/`0xE` y `6`/`0xF` llegan por `UiInput_Trigger` (`0x002B902C`);
`UiInput_Trigger2` (`0x002BFFBC`) se consulta con ID 0 en la compuerta de
confirmación. Ambos validan IDs lógicos (`< 0x1F`) y consultan estado global y
una tabla de resultados. La rutina `0x001078D8` deriva 31 estados lógicos en
`0x004E3C58` desde la configuración/máscaras en `0x004E3C28`; la consulta
`0x001FF830` lee las máscaras por ID en `0x004E3C48` y las compara con el estado
de la fuente seleccionada (`0x004099C0` o `0x004650A0`). No se encontraron
valores de máscaras ni bindings físicos inicializados en archivos seguidos por
Git: la estructura es recuperable estáticamente, pero la correspondencia con
teclas/gamepad aún necesita captura runtime. En H0, A abrió Audio Settings, lo
que concuerda con ID lógico 0 de confirmación.

## Dependencias y calidad de evidencia

- **Evidencia estática:** listado ARM del callback `0x001E989C`, constructor
  `0x001EB02C` y referencias de código. La versión C++ legible del callback está
  desactivada con `#if 0`; el callback compilado y el constructor son asm
  exacto, así que esto todavía no constituye reconstrucción semántica activa.
- **Evidencia runtime H0:** Azahar cargó batch 4 y se observó el recorrido
  título → Audio Settings → título. El monitor detectó entradas de
  `state_flags` y `two_word_copy`; los hits sólo acreditan ejecución, no
  equivalencia de comportamiento. Ver [H0](H0-reproducible-test-base.md).
- **Presentación pendiente:** los callbacks registrados `0x0020FD5C` y
  `0x0021F36C` son entradas embebidas en spans mayores
  (`battle_func_0020f564` y `shopMain_DrawDown`); el análisis acotó ambos cuerpos
  a 44 bytes, seguidos por el literal del global, y ambos ponen a 1 el byte
  `work+4`. `0x002CA7A8` es una función independiente de 968 bytes seguida por
  28 bytes de datos. Los límites se consideran de confianza alta por referencias
  del constructor/listado, pero el ledger aún conserva los spans exteriores en
  dos callbacks. No atribuir todavía una reconstrucción de dibujo al menú.
- **Estado inicial:** el constructor no escribe `work+0x9C`, pero la cadena de
  asignación sí inicializa el bloque: `AsdMem_AllocAlign` (`0x002C54F0`) llama
  `0x002C3B48` con el puntero devuelto y el tamaño solicitado `0xA0`; esa rutina
  limpia la región mediante stores de cero y/o el bucle de `0x002C4B30`.
  Por tanto el primer callback empieza en estado 0. El reset posterior a estado
  5 en `0x001EA470` no es el origen del estado inicial.
- **H1-C, piloto aislado:** el bloque inline `0x001E9DAC..0x001E9DC0` normaliza
  el cursor provisional con aritmética signed y guarda sólo `work+8`. El
  candidato C++ igualó el bloque ARM para `-1..4`; un control `raw % 4` fue
  detectado para `-1`. Esto no modifica ni reconstruye activamente el callback
  de 3924 bytes. Ver el informe `build/semantic-equivalence/title-cursor/`.
- **H1-C, familia de navegación:**
  `experiments/semantic_equivalence/title_navigation_family_candidate.cpp`
  modela las compuertas de disponibilidad, los pares de triggers lógicos
  anterior/siguiente con short-circuit, normalización del cursor, caché
  `work+0xC` y la llamada visible al evento `0x0100016C`. El harness ejecuta
  las ventanas ARM originales con respuestas de trigger controladas y un stub
  observacional explícito para el evento. Pasó 11 casos dirigidos y 256
  combinaciones sobre cursor/caché válidos y máscaras de triggers; las tres
  pruebas enfocadas pasan. No modela el interior del evento, los bindings
  físicos ni el callback completo; no está integrado en producción.
  La auditoría estática está en
  [`title_navigation_family_audit.md`](../../experiments/semantic_equivalence/title_navigation_family_audit.md).
- **H1-C, familia táctil:**
  `experiments/semantic_equivalence/title_touch_family_candidate.cpp` modela
  sólo las dos pasadas de estados táctiles sobre las cuatro regiones. Ejecuta
  la ventana ARM `0x001E9E4C..0x001E9EB8` con respuestas controladas por handle y
  coincide en 2,592 vectores de estados estables más flag inicial. El primer
  estado 1/2 gana en el primer barrido; en el segundo, el último estado 6 gana
  y fija `work+0x63`. Tres pruebas pasan. Se asume que el helper devuelve el
  mismo estado entre consultas; no se verifican coordenadas, hitboxes ni
  comportamiento táctil real en Azahar.
- **H1-C, continuidad navegación→animación→touch:**
  `tools/title_callback_continuity_experiment.py` ejecuta en una sola máquina
  las ventanas ARM de navegación, la animación VFP original y el barrido touch,
  con el bloque de trabajo y el estado FP compartidos. En tres perfiles
  estables coincide la composición de navegación C++ + puente ARM + touch C++;
  un cuarto perfil ARM-only prueba respuestas táctiles variables en las doce
  consultas. Tres pruebas pasan. Esto no cubre el camino de transición de
  widgets posterior ni habilita un reemplazo completo del callback. El mapa de
  dependencias está en
  [`title_callback_composition_audit.md`](../../experiments/semantic_equivalence/title_callback_composition_audit.md).
- **H1-C, familia de ayuda/presentación:**
  `tools/title_help_presentation_experiment.py` ejecuta el caller ARM
  `0x001EA12C..0x001EA15C` con `TitleTable.tbb` real. Para los cuatro índices,
  el puntero observado coincide con la cadena de ayuda correcta y prepara el
  color `0x323232FF`; tres pruebas pasan. La comparación se detiene antes de
  `Camp_SetSlotMessage`: no valida renderer ni texto visible en Azahar. Ver
  [`title_help_presentation_audit.md`](../../experiments/semantic_equivalence/title_help_presentation_audit.md).
- **H1-C, ruta sintética transición→ayuda:**
  `tools/title_transition_ready_path_experiment.py` ejecuta ARM original desde
  `0x001E9FD4`, atraviesa ambos predicados de readiness, toma la rama directa
  con `work+0x94=1` y continúa por los getters TBB originales hasta el límite
  previo a `Camp_SetSlotMessage`. Para los cuatro índices selecciona las
  cadenas reales y el color esperado; una prueba enfocada pasa. Es una ruta
  sintética de control, no el camino de transición visual: no entra al bloque
  mutador `0x001EA070`, no valida valores runtime-normal ni renderer. Ver
  [`title_transition_ready_path_report.md`](../../experiments/semantic_equivalence/title_transition_ready_path_report.md)
  y la [auditoría de readiness](../../experiments/semantic_equivalence/title_transition_ready_audit.md).
- **H1-C, rama mutadora continua:**
  `tools/title_transition_mutator_experiment.py` ejecuta 111 PCs ARM desde
  `0x001E9FD4` por `0x001EA070..0x001EA128`, consulta los getters TBB originales
  con la tabla real y se detiene antes de `Camp_SetSlotMessage`. En una ruta
  sintética con salidas tempranas de readiness/fade se observaron 38 lecturas
  y exactamente seis escrituras (flags de ambos handles, dos bytes anidados,
  `work+0x98` y `work+0x94`); llega a la cadena correcta para selección 0 y
  prepara `0x323232FF`. No se llamaron ni stubearon callbacks indirectos. Una
  prueba enfocada pasa. Esto no valida el camino de gates positivos, estado
  runtime-normal, renderer ni comportamiento visual en Azahar. Ver
  [`title_transition_mutator_experiment.md`](../../experiments/semantic_equivalence/title_transition_mutator_experiment.md).
- **Datos disponibles:** `/title/TitleTable.tbb` (880 bytes) está extraído a un
  directorio ignorado bajo `build/semantic-equivalence/real-assets`. Una lectura
  puntual y de solo lectura del CCI descifrado confirmó también los BAM que el
  caller carga: `title_top1.bam` (778,496 bytes; SHA-256
  `109c1ce81f06bb90484dda4e685564028b593667a5f16493d44157efe7682e12`) y
  `title_top2.bam` (774,272 bytes; SHA-256
  `eaa252616f8ba61ecda915cd1d381e2c4374fa78eb6289b86d6aa0358b5b904f`). El
  cálculo de offsets se validó contra el hash conocido de `TitleTable.tbb`;
  los BAM no se escribieron ni modificaron. Ambos tienen wrapper `ATBC`,
  `MDLSIGN` en `+0x80` y `CGFX` en `+0x100`. Un recorrido de solo lectura de
  los diccionarios CGFX identificó en cada BAM un modelo, siete texturas y un
  grupo de cada animación esquelética, material y visibilidad; `title_top1`
  contiene canales de 150 cuadros y `title_top2` de 1200. Todavía no reconstruye
  los objetos fuente/tracks que recibe el loader ni su byte de tipo. La traza
  estática confirma que `AsdAnim_SetupTrack` lee `source+0x10` ya en el objeto
  runtime, mientras CANM almacena el tipo del miembro en otra estructura
  (`member+0x08`); no se probó una correspondencia entre ambos. Se encontraron
  seis callers directos de setup, todos con referencias/nodos ya resueltos, pero
  no una escritura que explique el byte ni una asociación runtime por categoría.
  Ver las auditorías [serializada→track](../../experiments/semantic_equivalence/title_bam_track_source_type_mapping_audit.md)
  y [callers del loader](../../experiments/semantic_equivalence/title_canm_source_type_trace.md).
  La traza adicional de constructores confirma que los callers de modelo
  toman los targets de tablas relativas mesh/draw; los `AsdRes_Create` cercanos
  producen handles de nombre distintos, no esos targets. La materialización
  de las tablas aún pasa por un loader no identificado. Ver
  [origen de los targets de modelo](../../experiments/semantic_equivalence/title_track_source_constructor_trace.md).
  Cámara,
  entorno y texturas del
  título siguen sin extraerse. No se encontró
  un script `.bf` de título;
  formato y ubicación del evento `0x0100016C` y del destino AOC siguen abiertos.
  El inventario se reproduce sin extraer ni escribir los BAM con
  `python tools/title_bam_inventory.py --cci "<CCI-descifrado>" --romfs-index extracted/romfs_index.json`;
  valida NCSD/NCCH y el hash ancla de `TitleTable.tbb`, y limita la salida a
  nombres/tipos de animación, cuadros y cantidad de pistas. Las cinco pruebas
  de `tests/test_title_bam_inventory.py` pasan con `SMT4_DECRYPTED_CCI` definido
  para habilitar su caso de integración; sin esa variable, la prueba local se
  omite y las cuatro pruebas sintéticas siguen ejecutándose.
- **Contrato TBB confirmado estáticamente:** `Tbb_GetSubTable` valida magic
  TBCR, índice menor que `table_count`, resuelve `container + header_size +
  table_offsets[index]` y exige magic TBL1. `Tbb_GetPayloadData` devuelve
  `table+0x10` para TBL1 válido; `Tbb_GetRowCount` devuelve
  `payload_size / row_stride` (truncado), o 0 si el puntero/magic/stride falla.
  Ninguna rutina recibe el tamaño de archivo, por lo que no valida límites del
  contenedor o payload. Hay callers que usan el count para acotar filas en
  `src/ui/ui_runtime.cpp` y `src/camp/title_flow.cpp`.
- **Herramienta de inspección:** `tools/inspect_assets.py` ahora sigue el arreglo
  de offsets y los campos TBL1 anteriores, en vez de asumir tablas consecutivas
  y restar 16 del tamaño. Sus dos pruebas sintéticas pasan. Además,
  `Tbb_GetPayloadData` fue comparada contra la referencia ARM en 70 casos
  sintéticos por semilla y dos tablas reales por semilla; `Tbb_GetSubTable` en
  71 sintéticos por semilla y tres casos reales; `Tbb_GetRowCount` en 72
  sintéticos por semilla y dos tablas reales. En total son 426 comparaciones
  sintéticas y 14 reales en dos semillas. Los controles negativos dirigidos
  fueron detectados; ver las fichas de
  [payload](../function-records/0x002c0e9c.md),
  [subtabla](../function-records/0x002ac2f4.md) y
  [conteo de filas](../function-records/0x002c0e4c.md). El formato está descrito en
  [architecture.md](../architecture.md).
- **Límite del piloto ARM:** el runner configurado para el lote general acepta
  sólo hojas cuyo código
  entero termina en `bx lr` y rechaza operandos relativos a PC, llamadas y
  relocaciones. Los getters originales usan literales PC-relativos y
  `Tbb_GetRowCount` transfiere control a una rutina de división; por tanto no se
  deben añadir simplemente como nuevos candidatos al piloto configurado. Ya se
  añadió un validador separado para blobs con ramas locales y LDR literales en
  su cola de datos, y el runner permite elegirlo explícitamente para el código
  reemplazo. Pruebas sintéticas verifican aceptación/rechazo y ejecución de un
  literal después de reubicar el blob. Un modo TBB aislado ejecuta los tres
  getters, incluyendo fixtures aleatorios reproducibles por función y semilla.
  Para `Tbb_GetRowCount`, el oráculo sigue el tail-branch al helper exacto
  `0x002C6C10` dentro del `code.bin` fijado por hash; no se habilitaron branches
  externos genéricos. También se extrajo y probó el `TitleTable.tbb`
  real (880 bytes, SHA-256 `edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`),
  con dos subtablas y el índice límite. Los candidatos no admiten llamadas
  externas ni relocaciones.

## Pruebas de aceptación

1. Partir del perfil controlado de H0, registrar hashes de CCI y `code.ips`,
   versión del emulador y estado de archivos del perfil. Confirmar en el log que
   el parche se carga. No usar ni modificar la partida del usuario.
2. Arrancar en el título y verificar menú visible, opción inicial Cargar
   partida, cuatro etiquetas y ayuda correspondiente.
3. Medir qué entrada física genera cada ID con capturas y trazas. Recorrer
   adelante/atrás y comprobar límites 0↔3; cada movimiento cambia exactamente
   una entrada y actualiza la etiqueta de ayuda. Repetir una vez para descartar
   que el resultado dependa del estado anterior.
4. Abrir Audio Settings y cancelar sin alterar valores. Confirmar retorno al
   título y selección esperada. Comparar los archivos del perfil antes/después;
   no debe aparecer escritura de partida ni cambio de opciones.
5. Hacer una prueba de toque sólo si el emulador ofrece entrada táctil
   reproducible; verificar selección y confirmación por separado.
6. No confirmar Nueva partida, no seleccionar un slot de guardado y no entrar a
   Add-On Content en el perfil de usuario. Añadir sus pruebas únicamente cuando
   haya perfil desechable/restaurable y destinos delimitados.

## Lotes y responsables

- **H1-A, límites y contratos:** límites de callbacks y origen del estado
  inicial documentados. La familia de navegación y las ventanas de Trigger/
  Trigger2 quedaron auditadas estáticamente en
  [`title_navigation_family_audit.md`](../../experiments/semantic_equivalence/title_navigation_family_audit.md);
  las máscaras crudas de los IDs 5/6 y E/F apuntan estáticamente a D-pad y
  Circle Pad arriba/abajo, con etiquetas HID inferidas. En Azahar, flechas
  configuradas como Circle Pad y T/G como D-pad movieron la selección y
  actualizaron la ayuda con toques aislados. El mapeo de mando físico, el alias
  lógico exacto, repetición al mantener y estado interno de inputs siguen
  pendientes. Ver
  [`title_input_binding_audit.md`](../../experiments/semantic_equivalence/title_input_binding_audit.md).
- **H1-B, dependencias TBB:** contratos y pruebas aisladas de
  `Tbb_GetPayloadData` (`0x002C0E9C`), `Tbb_GetSubTable` (`0x002AC2F4`) y
  `Tbb_GetRowCount` (`0x002C0E4C`) están completados para fixtures sintéticos
  y `TitleTable.tbb`, con controles negativos detectados. La ejecución original
  del row-count depende del helper exacto `0x002C6C10` en la imagen fijada por
  hash; su candidato de 132 bytes calcula división unsigned sin relocaciones.
  La ventana real del menú principal ya validó la integración de
  `Tbb_GetSubTable` y `Tbb_GetPayloadData` para selecciones 0–3 con el
  `TitleTable.tbb` extraído. `Tbb_GetRowCount` no participa en este caller.
- **H1-C, reconstrucción activa:** elegir sólo después del mapa de dependencias
  y contratos. Mantener sustituciones de comportamiento en rama/lote separado
  del ledger byte-identical y validar con pruebas de función e integración. El
  reductor de navegación, touch y selección de ayuda ya tienen pruebas
  aisladas por familia; navegación→animación ARM→touch pasa con estado
  compartido y una ruta sintética `0x001E9FD4`→TBB llega al límite de ayuda.
  El siguiente lote debe seguir la ruta mutadora con `work+0x94=0` y predicados
  positivos a través de `0x001EA070..0x001EA128`, usando cuerpos ARM y hooks
  explícitos para callbacks indirectos. Ya se cubrió sintéticamente el primer
  gate positivo: el cuerpo original `0x002872B0` ejecutó un `BLX` hacia un stub
  explícito (`bx lr`) con ABI/FP observados, y la ejecución continua llegó al
  lookup TBB de ayuda. Ver
  [`title_transition_positive_gate_report.md`](../../experiments/semantic_equivalence/title_transition_positive_gate_report.md).
  También se cubrió el segundo cuerpo positivo `0x0020FFAC`: resolvió una
  tabla/registro sintético indexado, registró un segundo `BLX` y llegó al mismo
  límite TBB/ayuda. Ambos callbacks son stubs explícitos `bx lr`, no los
  destinos reales del juego. Ver
  [`title_transition_second_positive_gate_report.md`](../../experiments/semantic_equivalence/title_transition_second_positive_gate_report.md).
  En el primer gate, dos casos separados reemplazaron el stub por candidatos
  originales. `0x0015555C`, asociado estáticamente con recursos tipo 0, ejecutó
  sus diez PCs ARM y devolvió el clamp esperado. `0x00151404`, asociado con
  tipo 1, ejecutó su ruta y callees alcanzados del `code.bin` fijado, también
  llegó al límite TBB y devolvió `s0=0.75`. Ninguno prueba cuál selecciona el
  título real: falta relacionar los BAM verificados con el track concreto y su
  byte de tipo/puntero runtime. El índice local confirma que
  `title_top1.bam` y `title_top2.bam` son precisamente los modelos cargados por
  el caller; eso todavía no revela los registros seleccionados. Ver
  [`title_transition_original_callback_report.md`](../../experiments/semantic_equivalence/title_transition_original_callback_report.md),
  [`title_transition_callback_00151404_report.md`](../../experiments/semantic_equivalence/title_transition_callback_00151404_report.md)
  y [`title_real_callback_target_audit.md`](../../experiments/semantic_equivalence/title_real_callback_target_audit.md).
  Para el segundo gate también se probaron en procesos sintéticos separados
  ambos candidatos originales en `0x00210010`: el de tipo 0 devuelve `s0=0.6`
  y el de tipo 1 devuelve `s0=0.25`; ambos llegan al mismo lookup TBB. La
  primera llamada de fade sigue siendo un stub explícito de requisito. Estos
  escenarios no demuestran qué puntero contiene el track real. Siguen pendientes
  los punteros/tipos runtime, un snapshot runtime-normal que justifique los
  valores sintéticos, renderizado e integración del callback completo. No
  equiparar el resultado sintético con la UI de Azahar. Ver
  [`title_second_gate_callback_candidates_report.md`](../../experiments/semantic_equivalence/title_second_gate_callback_candidates_report.md).
- **H1-D, integración segura:** repetir criterios 1–5, documentar dependencias
  originales aún llamadas y actualizar este archivo, el plan y el registro.

Asignación: principal coordina e integra; los subagentes deben tomar familias
no solapadas del H1 activo y entregar evidencia, límites y pruebas. Las hojas
semánticas ajenas al recorrido H1 pueden conservarse como experimentos laterales,
pero no cambian el hito ni su criterio de avance. No compartir cambios del
runner sin un único responsable.

## Pendientes y cierre

- Registrar en el ledger la delimitación ya auditada de los callbacks de
  dibujo. El origen de `state_9C` está resuelto por el clear de `0xA0` bytes en
  la ruta de asignación, aunque el constructor no lo escriba explícitamente.
- Medir la correspondencia entre IDs de trigger y botones; confirmar wraparound
  y actualización de ayuda mediante evidencia runtime.
- Determinar límites reales de las entradas de dibujo y localizar/interpretar
  datos/evento del flujo AOC.
- H0 valida que batch 4 se integra y abre/cierra Audio Settings. H1 no está
  cerrado: falta reconstrucción activa del alcance y pruebas de aceptación
  completas.

Recorrido integrado validado: parcial (sólo Audio Settings y retorno, por H0).
Lógica del alcance reconstruida: no.
Próxima acción: localizar el loader que materializa los targets de las tablas
mesh/draw y seguirlo hasta el objeto fuente que aporta `source+0x10`, o capturar
ese objeto después de `SetupTrack`;
el tipo serialized de CANM no está demostrado como ese byte. Ambos candidatos
del primer y segundo `BLX` ya cuentan con escenarios sintéticos de código
original por separado; falta sustituir el grafo sintético por
registros/argumentos reales y observar el callback runtime. La navegación
segura de teclado ya se verificó en Azahar; quedan por medir control físico,
alias lógico y repetición de entrada. Mantener separados los valores sintéticos de cualquier
afirmación runtime-normal. No extender el emulador a rutas que alteren partidas.
