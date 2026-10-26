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

La revisión estática del callee aclara que `0x0029F10C` no es sólo un setter de
color: `r0` selecciona texto o modo null de reset y `r1` lleva el color. En los
estados H1 2 y 5, el caller pasa `slot-0x3A payload + selection*0x56 + 0x16`
y `0x323232FF`; `titleConfig` llama el modo null con el mismo color. El callee
copia hasta dos líneas a su workspace (`+0x4D0` y `+0x510`), busca delimitadores
hasta 128 bytes y no comprueba el límite de cada línea. El archivo real
`TitleTable.tbb` está disponible bajo `build/semantic-equivalence/real-assets`
(880 bytes; SHA-256
`edd6bc1de5388e5689f797861ae6947c7c339f9b6bdb63d6c35951d72020fa41`). Sus cuatro
strings de ayuda tienen 36, 39, 25 y 28 bytes, caben en los slots nominales de
64 bytes y coinciden en una comparación offline del ARM original con candidatos
editables (`0x0029F10C` y copia `0x002C5FF4`): 189/189 casos incluyendo matriz de
copia y controles negativos. Es evidencia parcial; el test entrega directamente
los cuatro punteros de fila y no ejecuta la consulta TBB del caller, el render ni
el runtime. No se validaron otras localizaciones ni entradas largas. Ver el
[contrato del helper](../agent-work/h1-title-message-contract.md), la
[revisión del contrato](../agent-work/h1-title-message-contract-review.md), el
[informe del candidato](../agent-work/h1-title-message-candidate.md) y la
[revisión independiente de los datos reales](../agent-work/h1-title-message-real-asset-validation-review.md).

Una composición separada cubre ahora el seam del caller de estado 5: ejecuta
ARM original desde `0x001EA12C`, conserva la búsqueda TBB y la aritmética de
fila, y en la imagen candidata cambia sólo el `BL` de `0x001EA15C` para entrar
al helper C++ enlazado. Las cuatro selecciones reales pasan hasta el retorno
(4/4); un control que fuerza la fila equivocada se detecta. Esta ventana parte
de un frame sintético con selección válida y termina en `0x001EA160`: no cubre
readiness/entrada del callback completo, inicialización/lifecycle real,
renderizado ni runtime. Ver el [plan](../agent-work/h1-title-message-caller-composition-plan.md),
su [revisión independiente](../agent-work/h1-title-message-caller-composition-review.md)
y el [informe de composición](../agent-work/h1-title-message-caller-composition.md).

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
  Un experimento aparte para el adaptador de continuación corrigió el runner de
  cinco casos: el runner anterior parcheaba la entrada tanto en el supuesto
  modo original como en el candidato, así que su diferencial y revisión no son
  evidencia válida de ARM-original-versus-C++. La matriz corregida deja intacta
  la imagen original y pasó 258/258 casos de ventana inline (256 combinaciones
  cursor/caché/máscara y dos compuertas negativas), con un control de módulo
  signed detectado. Sigue usando frame sintético y stubs de disponibilidad,
  triggers y evento; excluye prólogo/epílogo, placement de producción y runtime.
  Ver la [revisión de la matriz](../agent-work/h1-navigation-adapter-matrix-review.md)
  y la corrección en
  [`h1-navigation-continuation-adapter-review.md`](../agent-work/h1-navigation-continuation-adapter-review.md).
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
- **H1-C, compuerta de preview:** el candidato experimental
  `experiments/semantic_equivalence/h1_preview_gate_candidate.cpp` reconstruye
  `Camp_IsPreviewReady` (`0x0025A2BC`) leyendo el slot global y respetando el
  orden de las dos banderas, el byte signed de busy y la llamada al helper
  `0x002BF9F0`. El original y el candidato compilado coincidieron en 52 casos
  dirigidos; tres controles detectaron offsets y polaridades incorrectos. La
  revisión independiente apoya el contrato acotado de la compuerta. El helper
  sólo se stubbea en su entrada: sus efectos internos, el ciclo de vida del
  objeto en `scene+0xD74`, la llamada dentro del caller completo y el runtime
  siguen sin validarse. No es un reemplazo integrado. Ver la
  [ficha de función](../function-records/0x0025a2bc.md), el
  [informe del candidato](../agent-work/h1-preview-gate-candidate.md) y la
  [revisión](../agent-work/h1-preview-gate-review.md).
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
  Además, hay candidatos experimentales editables para ambos callbacks: el
  tipo 0 (`0x0015555C`) coincide en 17 casos ARM sintéticos, con revisión
  independiente del límite interior y las banderas VFP; el tipo 1
  (`0x00151404`) coincide en diez retornos y conserva como límite de dominio
  una ruta infinita que falla en el helper original. En el candidato tipo 0,
  NaN no toma GT ni LO y vuelve sin clamp; el control C++ difiere en FPSCR,
  mientras el harness no mide todos los registros caller-saved. En ambos casos
  siguen sin probarse la selección del callback por la instancia viva, la
  llamada compilada desde el caller y el comportamiento runtime. Ver
  [`h1-type0-callback-candidate.md`](../agent-work/h1-type0-callback-candidate.md),
  [`h1-type0-callback-review.md`](../agent-work/h1-type0-callback-review.md),
  [`h1-type0-callback-correction-review.md`](../agent-work/h1-type0-callback-correction-review.md),
  [`h1-type1-callback-candidate.md`](../agent-work/h1-type1-callback-candidate.md)
  y [`h1-type1-callback-review.md`](../agent-work/h1-type1-callback-review.md).
  El helper de preview `0x002BF9F0` también tiene un candidato C++ experimental:
  tras corregir una omisión del store `+0x86`, la matriz ampliada coincide en
  21/21 fixtures sintéticos con cinco callees sustituidos por stubs. La revisión
  independiente confirma la cobertura de esas ramas locales y el control
  negativo, pero sigue siendo evidencia parcial: no prueba trazas de lectura,
  estado transitorio, los cuerpos de los callees, el ciclo de vida real ni el
  enlace runtime del callback. Ver
  [`h1-preview-helper-candidate-review.md`](../agent-work/h1-preview-helper-candidate-review.md),
  [`h1-preview-helper-branch-coverage-review.md`](../agent-work/h1-preview-helper-branch-coverage-review.md)
  y la ficha de función [`0x002bf9f0`](../function-records/0x002bf9f0.md).
  Dos dependencias directas ya tienen candidatos C++ con revisión independiente
  parcial: `0x002BDAC0` inicializa coordenadas/estado desde filas de 12 bytes y
  coincide en ocho fixtures de memoria válida; `0x002C00D4` implementa una
  carga/store ordinaria condicional y coincide en 135 casos de RAM alineada.
  Para `0x002C00D4`, el wrapper llama estáticamente a través de
  `0x002A2414` con `r0=0x00473530`; esto no demuestra su llegada desde un objeto
  H1 vivo. Ninguno de estos candidatos está integrado en producción, y el
  segundo no es atómico. Ver las fichas
  [`0x002bdac0`](../function-records/0x002bdac0.md) y
  [`0x002c00d4`](../function-records/0x002c00d4.md), junto con sus revisiones.
  Ya hay candidatos C++ separados para `0x002C615C` y tres actualizadores de
  tracks: sus diferenciales privados pasaron 368/368, 17/17, 22/22 y 24/24
  casos, con controles negativos detectados; las revisiones aceptaron como
  parciales traslación, escala y secuencia. La revisión del divisor también
  quedó aceptada como parcial. Devuelve cociente/resto en `r0/r1`
  y procesa con signo los operandos con bit alto; la ruta H1 usa delta signed y
  duración positiva. El candidato deja scratch bajo el SP restaurado en algunos
  casos, discrepancia documentada y pendiente de revisar. El track de
  traslación corrigió un contraejemplo inicial que requería preservar `+0x6A`.
  `0x002B1C8C` tiene su propia lógica de sentinels: el selector de fila `-2`
  reinicia, `-3` es un valor ordinario y el `-2` de secuencia no encuentra una
  entrada. Además, un compuesto privado del helper y el setter editable
  `0x002BDAC0` pasó 8/8 casos ejecutando el setter ARM original/candidato real;
  los otros cuatro callees seguían como stubs y el control detectó el store
  `+0x50` omitido. Su revisión independiente quedó aceptada como parcial.
  Después se compuso `0x002BF9F0` con las cinco dependencias directas
  (`0x002BDAC0`, `0x002C615C`, `0x002B1DFC`, `0x002B1FC0` y `0x002B1C8C`)
  enlazadas a sus candidatos C++ compilados, sin callees externos sustituidos.
  El primer diferencial pasó 17/17 y detectó el mutante del store `+0x50`, pero
  su fixture de selector usaba un offset incorrecto. El runner compartido se
  reparó después: el nuevo 17/17 usa las palabras en `+8/+0x24`, afirma los
  efectos del lookup correcto y volvió a detectar el mutante; una revisión
  independiente verificó las identidades y el resultado. Estos candidatos
  siguen experimentales: usan objetos sintéticos, no prueban lifecycle,
  binding/caller H1 en vivo ni runtime y no están promovidos a producción. Ver
  el [informe corregido](../agent-work/h1-preview-full-composition.md), su
  [revisión de la reparación](../agent-work/h1-preview-full-composition-fixture-repair-review.md),
  la [primera revisión](../agent-work/h1-preview-full-composition-review.md),
  el [compuesto previo con el setter](../agent-work/h1-preview-row-setter-composition.md)
  y estas fichas
  [`0x002c615c`](../function-records/0x002c615c.md),
  [`0x002b1dfc`](../function-records/0x002b1dfc.md),
  [`0x002b1fc0`](../function-records/0x002b1fc0.md) y
  [`0x002b1c8c`](../function-records/0x002b1c8c.md), junto con sus notas de
  trabajo.
  Una expansión aparte alcanza las dos combinaciones máximas permitidas por
  las compuertas originales (divisor + las tres actualizaciones comunes, y
  setter + esas tres actualizaciones) en tres fixtures sintéticos y detecta el
  mutante. Divide y setter son mutuamente excluyentes en una invocación. Su
  tercer caso usa `+8/+0x24` para el lookup y su revisión independiente fue
  aceptada como parcial. Ninguno de estos resultados prueba el caller, lifecycle
  u objetos runtime.
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
  - **Rebanada de estado 5 integrada (`h1-menu-slice-integration`, 2026-10-25):**
    tras auditar el borrador `#if 0` completo (`h1-main-callback-editable-readiness`
    y revisión independiente) y capturar en vivo los punteros de callback de
    los gates A y B en Azahar (`h1-track-runtime` y revisión independiente:
    `child = 0x086e2780`, `[object+0x4c] = 0x00151404`, `[object+0x50] = 0`,
    duración `+0x48 = 1200.0f` en `0x002872E4` y `0x00210010`), se promovió a
    producción la función C++ `H1_TitleMain_UpdateNavigationSlice` en
    `src/ui/ui_runtime2.cpp` e `include/camp/title_flow.h`, y se integró en la
    ventana de 54 palabras (`0x001E9D08..0x001E9DDC`) de `ui_func_001e989c`
    mediante un shim de continuación in-place que preserva el tamaño exacto de
    3,924 bytes y la identidad byte a byte fuera de la ventana (`config/functions.csv`
    actualizado a `non_matching`). El runner de integración
    `tools/h1_menu_slice_integration_experiment.py` pasó 258/258 casos desde la
    entrada real `0x001E989C` (256 combinaciones cursor×caché×máscara + 2
    compuertas negativas), el caso adversarial de mutación de puntero global,
    el control negativo de módulo signed y las 4 selecciones `0..3` de la
    composición transición/fade/TBB (`0x001E9FD4..0x001EA15C`) con el callback
    observado `0x00151404`, el helper de alpha `0x0029BDB4` y los getters TBB
    promovidos. En Azahar (`runtime-report.json`), la comparación original vs
    parcheado verificó el hit en vivo en `0x003FE720` y la coincidencia en los
    11 pasos de navegación (`1→2→3→0→3→2`), textos de ayuda en `0x001EA15C`,
    apertura de Audio Settings (`0x002F4CA0` → `0x001EA928`) y retorno por
    cancelación (`0x001EA3D8` → estado 5 en `0x001E9DE0`) sin alterar archivos
    de guardado ni `g_ConfigBytes`.
  - **Rebanada de confirmación y despacho de estado 5 integrada (2026-10-25):**
    se promovió la función C++ `H1_TitleMain_ProcessConfirmationSlice` en
    `src/ui/ui_runtime2.cpp` e `include/camp/title_flow.h` (444 bytes compilados),
    cubriendo comprobación de sonido de cursor, trigger de confirmación
    (`UiInput_Trigger2(0)`), guarda de opción 1 sin confirmar, evento de
    confirmación `Script_RequestEvent(0x0100016D)`, avance de parpadeo de cursor
    `Camp_AdvanceCursorBlink` y despachos hacia Estado 6 (Nueva Partida),
    Estado 7 (Cargar Partida), Estado 9 (Audio Settings) y Estado 11 (AOC). Se
    enlazó en `ui_func_001e989c` mediante un shim de continuación in-place de 115
    palabras (`0x001EA160..0x001EA328`) preservando el tamaño exacto de 3,924 bytes
    y la identidad 100% de los bytes restantes.
  - **Reconstrucción de `Tbb_GetDefaultTable18Payload` (`0x002C0E84`):**
    reconstruido como C++ limpio en `src/ui/tbb_loader.cpp` llamando
    `Tbb_GetGlobalSubTable(0x18, 0)` y `Tbb_GetPayloadData(table)` directamente,
    eliminando el peligroso stack fallthrough sobre `0x002C0E9C` y actualizando
    `config/functions.csv` a `non_matching`.
    Ver [`h1-menu-slice-integration.md`](../agent-work/h1-menu-slice-integration.md).

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
- El peligro de fallthrough de `Tbb_GetDefaultTable18Payload` (`0x002C0E84`) sobre
  `Tbb_GetPayloadData` (`0x002C0E9C`) fue completamente resuelto mediante su
  reconstrucción en C++ en `src/ui/tbb_loader.cpp`.
- Las dos rebanadas funcionales esenciales de H1 (navegación/wraparound y
  confirmación/despacho de estado 5) y sus dependencias TBB y alpha han sido
  reconstruidas en C++ editable e integradas con evidencia diferencial ARM,
  composición y runtime en Azahar.

Recorrido integrado validado: validado (rebanadas de navegación y confirmación
de estado 5, transiciones a Audio Settings y retorno, wraparound `0..3`, textos
de ayuda y despacho de opciones verificados en simulador y Azahar).
Lógica del alcance reconstruida: validada para el flujo de menú principal H1
(`H1_TitleMain_UpdateNavigationSlice`, `H1_TitleMain_ProcessConfirmationSlice`,
`Tbb_GetSubTable`, `Tbb_GetPayloadData`, `Tbb_GetDefaultTable18Payload` y
candidatos de track/alpha verificados).
Próxima acción: pasar al siguiente hito funcional (H2 - Guardado y carga / Save-Load).
