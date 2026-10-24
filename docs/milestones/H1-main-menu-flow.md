# H1 — Menú principal

Estado: mapeando; recorrido título → Audio Settings → título verificado en H0
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
inicialización ni se ha resuelto dónde se fija inicialmente el estado `0x9C`.

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
una tabla de resultados. Otros callers usan 5/6 como par de navegación, y en H0
la tecla A configurada abrió Audio Settings, lo que concuerda con ID 0 de
confirmación. No se encontró el mapeo de esos IDs a botones físicos dentro del
repositorio, por lo que navegación y asignación física aún requieren medición.

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
- **Estado inicial pendiente:** el constructor escribe otros campos del área de
  trabajo, pero no `work+0x9C`; el primer reset explícito a estado 5 está en
  `0x001EA470`. El estado cero por asignación BSS/heap es una hipótesis, no una
  conclusión respaldada por la evidencia reunida.
- **Datos disponibles:** se extrajo `/title/TitleTable.tbb` (880 bytes) a un
  directorio ignorado bajo `build/semantic-equivalence/real-assets`; cámara,
  modelos, entorno y texturas del título siguen sin extraerse. No se encontró
  un script `.bf` de título;
  formato y ubicación del evento `0x0100016C` y del destino AOC siguen abiertos.
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

- **H1-A, límites y contratos:** límites de callbacks documentados; quedan por
  resolver el origen del estado inicial, significado de triggers físicos y
  traza runtime de estados.
- **H1-B, dependencias TBB:** contratos y pruebas aisladas de
  `Tbb_GetPayloadData` (`0x002C0E9C`), `Tbb_GetSubTable` (`0x002AC2F4`) y
  `Tbb_GetRowCount` (`0x002C0E4C`) están completados para fixtures sintéticos
  y `TitleTable.tbb`, con controles negativos detectados. La ejecución original
  del row-count depende del helper exacto `0x002C6C10` en la imagen fijada por
  hash; su candidato de 132 bytes calcula división unsigned sin relocaciones.
  Falta probar integración de los tres getters en una ventana de caller segura.
- **H1-C, reconstrucción activa:** elegir sólo después del mapa de dependencias
  y contratos. Mantener sustituciones de comportamiento en rama/lote separado
  del ledger byte-identical y validar con pruebas de función e integración.
- **H1-D, integración segura:** repetir criterios 1–5, documentar dependencias
  originales aún llamadas y actualizar este archivo, el plan y el registro.

Asignación inicial: principal coordina e integra; subagentes pueden trabajar
H1-A/H1-B en archivos separados. No compartir cambios del runner sin un único
responsable.

## Pendientes y cierre

- Resolver caller del constructor y origen de `state_9C`; registrar la
  delimitación ya auditada de los callbacks de dibujo en el ledger. No se
  encontró escritura de `work+0x9C` fuera del constructor/state machine; el
  allocator revisado no muestra un clear explícito, así que el valor inicial
  sigue sin explicación.
- Medir la correspondencia entre IDs de trigger y botones; confirmar wraparound
  y actualización de ayuda mediante evidencia runtime.
- Determinar límites reales de las entradas de dibujo y localizar/interpretar
  datos/evento del flujo AOC.
- H0 valida que batch 4 se integra y abre/cierra Audio Settings. H1 no está
  cerrado: falta reconstrucción activa del alcance y pruebas de aceptación
  completas.

Recorrido integrado validado: parcial (sólo Audio Settings y retorno, por H0).
Lógica del alcance reconstruida: no.
Próxima acción: completar H1-A con el origen del estado inicial; medir IDs
físicos cuando Azahar se vuelva a abrir. En H1-B, preparar una ventana de caller
segura; no extender
el emulador a rutas que alteren partidas.
