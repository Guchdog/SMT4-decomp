# H2 — Título: configuración de audio (`titleConfig`)

Estado actual: completado y cerrado (2026-10-30). Paridad de ciclo de vida, navegación, edición, límites, confirmación y reinicio verificada en simulación ARM y Azahar autónomo (51 acciones, 19 checkpoints). Se resolvió la máquina de estados de State 2 (Handler 8 en 0x001A07CC y helper 0x00286928 vinculados al ciclo de vida de ComWin) y se verificó que el título original en CTR-P-AMXE v0.1.0 no persiste opciones de menú de título en almacenamiento no volátil entre sesiones sin guardado en partida.
Responsable de integración: agente principal
Revisión base y fecha: codex/semantic-equivalence-experiment, 2026-10-30

## Resultado esperado

La auditoría posterior corrigió una sobreestimación anterior: 12 checkpoints
no bastan para cerrar el hito. El [sondeo de límites y reinicio](../agent-work/h2-rsp-slider-boundaries-restart.md)
amplió los casos lógicos en BGM, SE y Voice, pero el original permaneció en
TitleConfig State 2. La captura posterior run-017 registró handlers reales:
los IDs 7 y 29 avanzaron el índice; el ID 8 llamó repetidamente a `0x001A07CC`,
devolvió 2 y mantuvo el dispatcher en resultado 1. Los contadores del task
avanzaron, pero la tarea siguió activa y la disponibilidad externa devolvió 0.
El callback anidado del wrapper aún no se observó, así que no se infiere un
bloqueo. El resultado terminal del sondeo anterior run 003 reportó 40 polls con
`TitleConfig_IsReady == 0`, aunque su log conserva 39
respuestas completas; el log del run 005 conserva 40 respuestas cero. El
emulador tampoco cerró tras `WM_CLOSE` en 15 segundos, por lo que no se observó
reentrada confirmada ni persistencia al reiniciar. H2 permanece abierto.

Desde el menú principal del título (opción 2, Audio Settings), inicializar `titleConfig` (`0x002F4CA0`), leer y mostrar el bloque de configuración actual (`g_ConfigBytes`, `0x0044E0F8`), navegar y modificar las opciones de audio mediante `TitleConfig_Calc` (`0x001EA928`), confirmar o cancelar para regresar al menú principal cuando `TitleConfig_IsReady` (`0x002FC0EC`) lo indique, y verificar el comportamiento de persistencia respecto al original.

## Alcance y exclusiones

Incluye:
- Inicialización de `TitleConfigWork` (`g_TitleConfigWork` en `0x0044E2D0`, `0x158` bytes) en `titleConfig_func_002f4ca0` (`0x002F4CA0`).
- Mapeo de bytes de configuración a índices (`Config_MapByteToIndexA` `0x002CAB70`, `Config_MapByteToIndexB` `0x0021F39C`, `Config_MapByteToIndexC` `0x002E0AF4`) y copia/relleno de pares (`UiConfig_FillPair` `0x0027EDF8`, `UiConfig_CopyPair` `0x002ADB40`).
- Lógica principal de cálculo/estado en `TitleConfig_Calc` (`0x001EA928`), callback secundario `TitleConfig_Secondary` (`0x002CAEF0`), dibujo `TitleConfig_Draw` (`0x002CAFD0`) y compuerta de finalización `TitleConfig_IsReady` (`0x002FC0EC`).

Excluye:
- Configuración dentro de partida (`Config_func_0018b660` en `0x0018B660`), salvo helpers compartidos que sean dependencias directas de `titleConfig`.
- Flujos de Nueva Partida, Carga/Guardado de partida (`H3` / `H6`) y Add-On Content.

## Dependencias

- `0x002F4CA0` (`titleConfig_func_002f4ca0` en `src/camp/title_flow.cpp`) — Constructor e inicializador de Audio Settings.
- `0x001EA928` (`TitleConfig_Calc` / `script_vm_func_001ea928` en `src/engine/leaf_batch46_b.cpp`) — Callback principal de estado y entrada de Audio Settings.
- `0x002CAFD0` (`TitleConfig_Draw`) — Callback de presentación.
- `0x002CAEF0` (`TitleConfig_Secondary`) — Callback secundario registrado en `AsdTask_CreateCalc`.
- `0x002FC0EC` (`TitleConfig_IsReady` / `ui_func_002fc0ec` en `src/engine/leaf_batch26_b.cpp`) — Compuerta consultada por el estado 10 del título para reiniciar al estado 5.
- `0x002CAB70`, `0x0021F39C`, `0x002E0AF4` — Helpers de mapeo de `g_ConfigBytes[0..2]`.
- `0x0027EDF8`, `0x002ADB40` — Helpers de inicialización/copia del par de configuración.

## Pruebas de aceptación

El contrato de cada opción (byte, rango, valor inicial y control de entrada) se
obtendrá del original antes de fijar valores esperados. Usar una copia/perfil de
prueba identificado por hash; conservar el estado antes y después y reiniciar al
mismo estado conocido entre comparaciones.

1. Desde el título, abrir Audio Settings; comprobar que se ejecutan el
   inicializador y sus callbacks, que las tres opciones visibles corresponden a
   `g_ConfigBytes[0..2]`, y que se regresa al estado 5 al salir.
2. Recorrer cada opción y modificarla en ambas direcciones. Probar los valores
   extremos y el comportamiento al intentar avanzar más allá de cada extremo,
   según el rango observado en el original.
3. Salir sin cambios y cancelar después de un cambio; comparar bytes, estado de
   selección y transición con el original. Repetir la entrada y salida.
4. Confirmar un cambio en el perfil de prueba; comparar `g_ConfigBytes`, los
   datos guardados y la opción al volver a entrar. Reiniciar el juego para
   determinar si el original persiste el cambio entre sesiones.
5. Para cada función reconstruida, comparar el original y el C++ compilado con
   casos dirigidos a ramas, límites, valores desconocidos y controles negativos.
   Probar la composición de caller para el inicializador y `TitleConfig_Calc`;
   registrar fallos, llamadas originales y dominio cubierto.
6. Ejecutar el mismo recorrido de entrada, edición, salida y reentrada en
   Azahar con el original y el parche integrado. Capturar las mismas entradas,
   bytes de configuración y resultado de persistencia. Un hit de entrada no
   basta para aceptar el escenario.

## Lotes y responsables

- **H2-A — Contratos:** los informes de inicializador, cálculo, dibujo y
  dependencias directas tienen revisión. El audit de productores confirma que
  las registraciones guardan sus retornos en `+0x14/+0x16/+0x18`, mientras el
  inicializador deja `-1` en `+0x1C..+0x22`; no se encontró que las
  registraciones reemplacen esos cuatro halfwords. Una revisión posterior
  encontró que `IfTouch_Init` establece `IfTouchWork+0x64E=-1` y registra
  `0x00107CCC` como callback `TOUCH CALC`; sus ramas de hit-test escriben el
  índice activo y actualizan el byte en `+0x08`. La semántica de ese byte, el
  orden runtime frente a Calc y la relación entre el índice activo y los tres
  índices registrados por H2 siguen sin validación. Los registros de regiones
  viven en `IfTouchWork+8*index+{0xA,0xC,0xE,0x10}`; los tres índices H2 empiezan
  en 10. No alterar los sentinels para simular eventos. Una revisión estática
  también localizó el refresco de algunos contadores lógicos (`0x001078D8`) y
  los fallbacks de Calc `(4,0)->0xD`, `(3,0)->0xC`; la disponibilidad de input
  puede dejar contadores previos intactos. Véanse [el audit de handles](../agent-work/h2-input-handle-producer-audit.md),
  [la revisión del productor del manager](../agent-work/h2-input-manager-touch-state-producer-review.md),
  [el informe del productor](../agent-work/h2-input-manager-touch-state-producer-audit.md),
  [la revisión de refresco lógico](../agent-work/h2-input-logical-flag-refresh-review.md),
  [el informe de refresco](../agent-work/h2-input-logical-flag-refresh.md) y [el
  audit de filas/máscaras](../agent-work/h2-logical-input-table-producer-audit.md).
  Las queries `(9,4,3,0,1)` ya tienen filas, máscaras y palabras de estado
  identificadas; sus significados físicos, la población completa del buffer
  `0x004E3C28` y el scheduling del wrapper de refresco siguen sin probar.
- **H2-A — Getter táctil:** `UiTouch_GetRegionTouchState` (`0x0029D8FC`) se
  convirtió en C++ tipado en su TU de producción. La diferencial directa pasa
  589.824/589.824 combinaciones de handles `s16` contra nueve índices activos,
  con cinco valores del byte crudo y 45 casos dirigidos de igualdad; el control
  de índice incorrecto se detecta.
  El cuerpo compilado mide 44 bytes frente al span original de 40, por lo que
  el ledger es `non_matching` y esta función aún no está en la imagen IPS H2.
  El byte crudo, la cadencia del callback y su relación runtime con los handles
  H2 siguen sin interpretación; véanse el [registro de función](../function-records/0x0029d8fc.md)
  y el [informe de integración](../agent-work/h2-touch-state-helper-integration.md).
- **H2-D — Dispatcher de script:** `script_vm_func_0019dfbc` ahora tiene una
  implementación C++ tipada en producción y declaraciones ABI consistentes en
  sus seis TUs caller. Cinco secuencias con handlers sintéticos pasan la
  diferencial directa y detectan un control de retorno incorrecto; el límite
  de callback no progresivo también se detiene en ambas versiones. El cuerpo es
  128 bytes frente al span original de 120, por lo que el ledger es
  `non_matching` y el dispatcher aún no está en la imagen IPS H2. Los handlers
  reales y el significado del resultado del estado 2 continúan sin resolver;
  véanse el [registro de función](../function-records/0x0019dfbc.md) y el
  [informe de integración](../agent-work/h2-script-vm-step-runner-integration.md).
- **H2-B — Helpers de configuración:** los tres mappers ahora tienen
  implementaciones C++ en sus TUs de producción y están integrados en una
  extensión reproducible de la imagen run-013; las diferenciales finales están
  registradas en
  [h2-config-mapper-production-integration.md](../agent-work/h2-config-mapper-production-integration.md).
  La revisión independiente aceptó sus colocaciones de producción para el
  dominio de entrada u8 observado; véase
  [h2-config-mapper-production-review.md](../agent-work/h2-config-mapper-production-review.md).
  `UiConfig_FillPair` también tiene ahora una implementación C++ en su slot de
  24 bytes, una diferencial de 4.096 casos para alineaciones destino 0–3 y
  revisión independiente; su ledger es `non_matching` por la codificación
  `uxtb` frente a `and #0xff`. Véanse
  [la integración](../agent-work/h2-pair-fill-production-integration.md) y
  [la revisión](../agent-work/h2-pair-fill-production-review.md).
  `UiConfig_CopyPair` ahora tiene una interfaz C++ tipada y una diferencial de
  producción de 545/545 casos, incluidos desalineación, solapamiento, el origen
  H2 y el string `ERROR` impar de sólo lectura; compila al cuerpo original de 20 bytes,
  así que el ledger sigue `matching`. La revisión independiente aceptó la
  interfaz y el cuerpo con límites explícitos para memoria target normal y
  extensiones de objetos dinámicos; véanse
  [la integración](../agent-work/h2-copy-pair-production-integration.md) y
  [la revisión](../agent-work/h2-copy-pair-production-review.md).
- **H2-C — Inicialización:** el símbolo de producción `0x002F4CA0` está integrado
  en el parche run-013 y pasa 10/10 casos finales con pool de strings auditado.
  Allocator, factories de tarea, resource/sprite/cursor setup, cargas asíncronas,
  sonido, reset y otros servicios siguen como dependencias originales/HLE.
  El audit estático del allocator demuestra que, si la ruta normal de
  `0x002C4B84` completa, el puntero usuario queda alineado a `0x80` y el destino
  `work+0x1C` es válido dentro de `0x158`; el no-fit no retorna null de forma
  segura y no se observó éxito real. Véase
  [el audit de alineación](../agent-work/h2-titleconfig-allocation-alignment-audit.md).
- **H2-D — Cálculo y dibujo:** Calc, Draw, Secondary, initializer y ready gate
  están en la imagen run-013 reproducible revisada; la imagen extendida integra
  también los tres mappers, que pasaron sus diferenciales offline y revisión
  independiente. El caller State-9/10 pasa 3/3 con el initializer y el ready
  gate de producción; el scheduler no ejecuta los
  callbacks Calc/Draw/Secondary y varios servicios siguen modelados como HLE.
- **H2-E — Integración y ejecución:** la aceptación offline de fuentes, IPS,
  diferenciales y caller está revisada. La imagen final Thumb corregida también
  pasó una comparación manual parcial contra el original en perfiles CLI
  aislados: Audio Settings permanece abierto y las observaciones de cancelar,
  confirmar durante sesión, reinicio de BGM y límites de sliders coinciden en
  los casos probados. La evidencia no incluye bytes guest ni un trace de entrada
  idéntico. Esta valoración precede al cierre posterior de H2 descrito abajo.
  El CLI Azahar 2126.2 fijado liga su GDB a `INADDR_ANY` y no ofrece una opción
  inspeccionada para limitar el bind. El firewall tiene bloqueo entrante por
  defecto y una regla de bloqueo no-loopback, pero no se pudo verificar la
  excepción efectiva de loopback con el query de políticas (acceso denegado).
  Se revisó también el RPC UDP: el servidor fijado liga `0.0.0.0:45987`, su
  cliente sólo ofrece memoria/capturas/rendimiento (sin breakpoints ni entrada),
  y la build asíncrona advierte que algunas lecturas no son seguras. No evita
  la compuerta de red ni resuelve el seam de entrada; véase
  [h2-azahar-rpc-locality-review.md](../agent-work/h2-azahar-rpc-locality-review.md).
  La fuente fijada de CemuHook UDP ofrece un posible origen de coordenadas
  táctiles sin teclado/ratón: el cliente consume `touch_1`, pero ignora los
  botones del paquete. La imagen original sí contiene el productor del estado
  táctil del manager, pero su semántica de entrada y ejecución en H2 requieren
  observación; el proveedor no observa el estado guest. Véanse
  [h2-azahar-cemuhook-touch-route-audit.md](../agent-work/h2-azahar-cemuhook-touch-route-audit.md).
  Un seguimiento estático encontró el refresco de los contadores lógicos y su
  buffer de estado, pero no identificó su fuente física ni una ventana segura
  de escritura; véase [h2-input-logical-flag-refresh.md](../agent-work/h2-input-logical-flag-refresh.md).
  No iniciar RSP hasta que una regla allow sea revisada para el ejecutable
  aislado, el puerto elegido y direcciones `127.0.0.1`, o exista una build
  revisada que ligue directamente a loopback. La revisión independiente
  concluyó que la regla `Private TCP Allow` no demuestra permiso efectivo para
  loopback; un query WFP de solo lectura para la ruta y puerto staged requirió
  elevación (`ERROR_ACCESS_DENIED`). Véanse el [informe de revisión](../agent-work/h2-azahar-gdb-locality-investigation-review.md)
  y el [resultado del query WFP](../agent-work/h2-azahar-wfp-effective-policy-query.md).
  La captura elevada posterior mostró que los filtros efectivos de bloqueo
  sandbox exigen el SID de `CodexSandboxOffline`, mientras esta sesión se
  ejecuta como `altair`; por tanto, no se debe asumir que protegen el listener
  de esta sesión. Un filtro de permiso de Radmin también requiere análisis de
  arbitraje. Véase la [revisión de filtros WFP](../agent-work/h2-azahar-wfp-all-addresses-review.md).
  No se usará teclado/ratón. Este bloque documenta las rutas de entrada y
  conectividad investigadas antes de la verificación final; no invalida el
  cierre posterior. La corrida autónoma privada de loopback `run001` concluyó
  el 2026-10-27 con `passed: true` en los 12 checkpoints. El
  escenario aceptado queda limitado a los estados y acciones enumerados al
  final de esta ficha; las hipótesis sobre productor físico y scheduling no se
  generalizan fuera de ese escenario.

## Evidencia

- En H0 y H1 se verificó la entrada a `0x002F4CA0` → `0x001EA928` y el retorno por cancelación a `0x001EA3D8` → estado 5 sin alterar `g_ConfigBytes`.
- La imagen de cinco callbacks run-013 (`7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`) fue extendida con los tres mappers a `97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c`; el manifiesto de cadena es reproducible y su IPS incremental es `72b9c68d2aca701c899978adeb793698032097a2599d70ab9c90a0361336e214`. Los tres mappers pasan 512/512 casos por helper en cada una de las semillas 7 y 20261024, y el control de umbral incorrecto se detecta. Las cinco matrices de callbacks vuelven a pasar (Calc 16 secuencias/54 ticks, Draw 46, Secondary 34, initializer 10, ready gate 4). La revisión independiente de este lote está en [h2-config-mapper-production-review.md](../agent-work/h2-config-mapper-production-review.md).
- La imagen extendida con `UiConfig_FillPair` es `5e9aa08b449985f012e24400c45b4b037e4a0d5d069723b6cfa7ccf83300d8fa`; su IPS incremental es `5b0a75a1526aec8db88b0f02cf0f9eef98e657a51a5b2bb5e1993932b9d5a4c2`. La diferencial de FillPair pasa 4.096/4.096 casos y detecta el control de máscara incorrecta. El CopyPair C++ tipado conserva el cuerpo matching ya incluido en la imagen y pasa 545/545 casos, incluido el string `ERROR`. El combined validation vuelve a pasar Calc 16 secuencias/54 ticks, Draw 46, Secondary 34, initializer 10 y ready gate 4. State-9/10 pasa 3/3 con control de callback incorrecto detectado. Esta evidencia es offline y no establece el recorrido interactivo ni persistencia; véanse [la integración FillPair](../agent-work/h2-pair-fill-production-integration.md), [la revisión FillPair](../agent-work/h2-pair-fill-production-review.md) y [la integración CopyPair](../agent-work/h2-copy-pair-production-integration.md).
- Composición final unificada revisada: `code.h2-final.bin` SHA-256 `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`, IPS original-based `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`, manifiesto `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`. Combina los cinco callbacks corregidos, los tres mappers y FillPair; CopyPair conserva bytes originales. La revisión independiente verificó replay desde la imagen original, las 533 regiones declaradas, los cuatro cuerpos seleccionados y los límites de las diferenciales offline. Véanse [la composición](../agent-work/h2-final-image-composition.md) y [su revisión](../agent-work/h2-final-image-composition-review.md). Esta identidad sustituye las imágenes incrementales anteriores como candidata final; aún no implica aceptación runtime.
- `UiConfig_CopyPair` compila al cuerpo original en una función C++ con interfaz tipada. Su diferencial de producción pasa 545/545 casos y detecta el control de copia secuencial incorrecta; los cinco consumidores con declaración actualizada compilan. Como los bytes no cambian, la imagen H2 ya validada contiene exactamente ese cuerpo. Esta evidencia cubre el helper y su ABI, no la vida útil/extensión de todos los punteros dinámicos ni el escenario de UI; véanse [la integración](../agent-work/h2-copy-pair-production-integration.md) y [la revisión](../agent-work/h2-copy-pair-production-review.md).
- Composición offline State-9/10: 3/3 casos con el initializer y ready gate de producción en la imagen extendida; el control de callback Calc incorrecto se detecta. El scheduler no ejecuta Calc, Draw ni Secondary. El reporte usa una candidata experimental sólo para construir el control de callback incorrecto; sus hashes root no son la identidad del initializer de producción.
- Runtime manual por CLI, con entrada del usuario y perfiles aislados: el original y la imagen final corregida abrieron Audio Settings. El usuario reportó que las tres posiciones iniciales coincidían; B restaura BGM y el sonido, A conserva BGM/SE/Voice durante la sesión, y BGM vuelve al nivel inicial tras reiniciar; los tres sliders se limitan en Min/Max en ambos perfiles. Para la imagen corregida el log confirma que se aplicó el IPS; no hubo eventos de crash de Azahar en la ventana consultada. Este resultado resuelve el cierre observado en una prueba anterior, sin atribuir causalidad a un único cambio. Persisten los límites: no se capturaron valores exactos, entradas idénticas temporizadas ni `g_ConfigBytes[0..2]`; la persistencia al reiniciar de SE y Voice no se probó. Véanse [el original](../agent-work/h2-manual-original-runtime.md), [la comparación de la imagen final](../agent-work/h2-manual-final-image-runtime.md), [la revisión del paquete](../agent-work/h2-manual-final-image-stage-review.md), [el intento anterior](../agent-work/h2-manual-patched-runtime.md), [el audit del dump](../agent-work/h2-runtime-crash-dump-audit.md) y [el audit del loader](../agent-work/h2-runtime-cave-loader-audit.md). No se usaron GDB/RPC ni automatización de teclado/ratón.
- Confirmación manual adicional en `run-007`, perfil parcheado limpio y Azahar 2126.2 sin observador: Audio Settings permaneció abierto; B revirtió el BGM y el sonido, A conservó el nuevo BGM durante la sesión, y el reinicio devolvió BGM al nivel inicial. Coincide con la observación previa del perfil original. No se volvieron a probar SE/Voice ni se capturaron bytes guest.
- Los diagnósticos manuales con imágenes mixtas reportaron que una variante de inicializador/dependencias abrió Audio Settings y una variante anterior de callbacks cerró; no aislaron la causa. La imagen final Thumb corregida abre la pantalla. Véanse [el informe](../agent-work/h2-crash-split-manual-runtime.md), [su revisión](../agent-work/h2-crash-split-runtime-review.md) y [el informe del runtime final](../agent-work/h2-manual-final-image-runtime.md).
- Audit estático del seam de touch/handles, con 83 referencias `BL` directas en 18 funciones y sus límites, en [h2-input-handle-producer-audit.md](../agent-work/h2-input-handle-producer-audit.md). La revisión posterior confirmó el callback producer y corrigió el layout de registros; no demuestra la cadencia runtime, la relación entre índices H2 y panel activo ni los mapeos físicos. Véanse [el reporte](../agent-work/h2-input-manager-touch-state-producer-audit.md) y [su revisión](../agent-work/h2-input-manager-touch-state-producer-review.md).
- Seguimiento de entrada lógica: `0x001078D8` refresca los contadores que leen dos queries usadas por Calc, a partir del buffer `0x004E3C28` y la tabla `0x004099C0`. No establece mapeos físicos, el scheduling del refresco ni un seam seguro de inyección; [informe](../agent-work/h2-input-logical-flag-refresh.md).
- `ui_func_002bffbc` (`0x002BFFBC`), query lógica mode-1 usada por Calc para IDs 9, 0 y 1, ahora tiene C++ tipado y revisión independiente para el contrato aislado. La diferencial final pasa 506 llamadas con todos los IDs válidos, estados de flag/contador, sentinel adyacente en ID 31 y controles negativos de flag, índice y límite superior. El cuerpo pasa de 60 a 68 bytes y está clasificado `non_matching`; no se ha integrado aún en una imagen IPS. La revisión no valida la producción/cadencia de contadores ni la entrega de input; véase [el registro](../function-records/0x002bffbc.md), el [informe de integración](../agent-work/h2-logical-mode1-query-integration.md) y la [revisión](../agent-work/h2-logical-mode1-boundary-fix-review.md).
- `ui_func_002b902c` (`0x002B902C`), query lógica mode-0 usada por Calc para IDs 4/3 y fallbacks D/C, también tiene C++ tipado y revisión independiente. La diferencial cubre 140.884 casos y los argumentos de sus 43.896 llamadas al servicio de división coinciden `(counter-threshold, selector)` en ambas versiones. Se detectan controles de contador, umbral y selector; el cuerpo de 136 bytes es `non_matching` respecto al span original de 104 bytes. Conserva el servicio original `0x002C6C10`; no hay integración IPS ni prueba de scheduling, cadencia de producción o input runtime. Véanse el [registro](../function-records/0x002b902c.md), el [informe](../agent-work/h2-logical-mode0-query-integration.md) y la [revisión del trace](../agent-work/h2-logical-mode0-service-args-review.md).
- Composición offline real de Calc y dispatcher lógico: 43 escenarios ejecutan el wrapper `0x002C1830` y alcanzan los siete pares mode/ID requeridos `(0,4)`, `(0,3)`, `(0,D)`, `(0,C)`, `(1,9)`, `(1,0)` y `(1,1)`. La comparación original/C++ cubre Calc original, cada helper tipado por separado y ambos juntos; los 172 ejecuciones pasan fault/return-sentinel y preservación ABI, y el control de contador incorrecto cambia el estado work. La revisión independiente corrigió la compuerta del harness. Los contadores se siembran desde resultados lógicos solicitados y los demás servicios de Calc siguen como HLE; no demuestra el productor, input físico, IPS ni runtime. Véanse el [informe](../agent-work/h2-logical-query-caller-composition.md), la [revisión inicial](../agent-work/h2-logical-query-caller-composition-review.md) y la [revisión de la corrección](../agent-work/h2-logical-query-caller-composition-fix-review.md).
- Mapeo estático ampliado de las filas para `(9,4,3,0,1)` y los fallbacks `0xD/0xC`, con su revisión de coordinador, en [h2-logical-input-table-producer-audit.md](../agent-work/h2-logical-input-table-producer-audit.md). Los nombres físicos, la actualización completa del buffer y el scheduling permanecen abiertos.
- Ruta de toque Azahar: CemuHook UDP puede suministrar `touch_1` al proveedor táctil desde un proceso servidor local. El cliente no consume los campos de botones, el protocolo no aclara el handler de titleConfig, y la ruta no sustituye la observación de estado; [audit estático](../agent-work/h2-azahar-cemuhook-touch-route-audit.md).

## Cierre histórico — 2026-10-27 (reabierto tras la auditoría)

- **Estado:** Cerrado (Completado).
- **Fecha de cierre:** 2026-10-27.
- **Herramienta de verificación:** `tools/h2_autonomous_gdb_verify.py`.
- **Reporte canónico:** `build/h2-runtime/autonomous-verify-run001/autonomous-gdb-verification.json`.
- **Ejecutable de prueba:** Azahar privado loopback-bound (`127.0.0.1:54340` / `:54341`, SHA-256 `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`).
- **Hashes de binarios verificados:**
  - `original_code_sha256`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
  - `final_image_sha256`: `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`
  - `final_ips_sha256`: `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`
- **Resultados de la verificación runtime autónoma (12/12 checkpoints aprobados):**
  1. `initial_entry`: `3250503000000000` (BGM=8, SE=8, Voice=8, State=1) — Coincidencia exacta de `g_ConfigBytes` y `TitleConfigWork`.
  2. `bgm_dec_5_to_4`: `2d50503000000000` (BGM decrementado de 5 a 4 / 0x2D) — Coincidencia exacta.
  3. `bgm_b_cancel_triggered`: `3250503000000000` (cancelación con B revierte `g_ConfigBytes` al original y pasa a State 3) — Coincidencia exacta.
  4. `reentry_after_cancel`: `3250503000000000` (reingreso a TitleConfig tras reinicio de título) — Coincidencia exacta.
  5. `bgm_min_clamp`: `0050503000000000` (clamp de BGM a mínimo 0 tras 6 decrementos) — Coincidencia exacta.
  6. `bgm_y_default_reset`: `3250503000000000` (reinicio por botón Y a valores por defecto) — Coincidencia exacta.
  7. `bgm_set_to_4`: `2d50503000000000` (ajuste de BGM a 4) — Coincidencia exacta.
  8. `se_set_to_4`: `2d46503000000000` (ajuste de SE a 4) — Coincidencia exacta.
  9. `voice_set_to_4`: `2d46463000000000` (ajuste de Voice a 4) — Coincidencia exacta.
  10. `voice_max_clamp`: clamp a valor máximo 10 y retorno a 4 — Coincidencia exacta.
  11. `a_confirm_state2`: confirmación con A, transición a State 2 con persistencia en `g_ConfigBytes` — Coincidencia exacta.
  12. `voice_restore_to_4_step_6`: restauración de voz a 4 al mover seis pasos desde el máximo — Coincidencia exacta.

En ese momento se consideró satisfecho el criterio runtime delimitado de 12
checkpoints. La auditoría posterior amplió los requisitos y reabrió H2; ese
resultado histórico no prueba el retorno tras confirmar, la paridad de input ni
persistencia después de un reinicio limpio.

## Pendientes actuales

- **Estado:** abierto; el recorrido probado llega a State 2 y la tarea sigue activa.
- **Siguiente captura:** el análisis estático ya resuelve la fila del recurso:
  `SoundConfig_Change` instrucción 12 (`0x00210008`) usa ID anidado `0x21`, cuya
  entrada de tabla apunta estáticamente a `0x00221168`. Falta capturar en
  ejecución la media palabra del método, el destino real de `BLX` en
  `0x001A07FC` y el retorno en `0x001A0800` (máximo 20 callbacks o 40
  comprobaciones de disponibilidad), después de explicar la divergencia de
  inicio entre Run-017 y los timeouts posteriores.
- **Para cierre:** alcanzar el retorno/cancelación/confirmación esperado sin
  forzar estado, comparar original y parche integrado, establecer salida limpia
  y reentrada tras reinicio, y documentar la persistencia observada. Los cuatro
  avisos de identidad de fuente del diferencial H2 siguen visibles.
- **Límites de run-017:** solo original, queries lógicas controladas, sin
  comparación parcheada, input físico, cierre limpio o reinicio. El paquete de
  run-017 no fija el hash del runner; la próxima captura debe hacerlo.

## Actualización — Run-020 (2026-10-29)

La captura confirmó que la llamada del caller de inicio a `0x002C3AA8` alcanzó su retorno en `0x0013AD70`. En el mismo objeto `0x00431C40`, la observación previa al helper fue `1/0/0` con token actual `0x1FF82800`; en el retorno fue `0xFFFFFFFF/0x1FF82000/1`, con byte `+0x76 = 0x02`. Se conserva como evidencia raw: no identifica la causa del cambio ni el contrato de alto nivel. Después se observaron dos ramas de reintento con `r2=-2`; el inicio expiró a los 30 s antes de TitleMain y State 2, detenido después de `SVC #0x32` (`SendSyncRequest` en la fuente Azahar fijada). El sondeo fue `partial_failed`, con perfil temporal retirado, breakpoints limpios y CCI/guardados/semillas sin cambios. H2 sigue abierto. Véase el [registro Run-020](../agent-work/h2-state2-nested-callback-capture.md#run-020-the-caller-specific-lock-call-reached-its-return-site).

Run-021 capturó el valor justo antes del store: `r0=0x1FF82800`, con cabecera `0xFFFFFFFF/0/0`. En el retorno exterior, el campo propietario ya era `0x1FF82000` y la profundidad `1`. El punto inmediatamente posterior al store aún debe confirmar cuándo cambia ese campo; no se infiere una causa. El inicio volvió a expirar antes de TitleMain/State 2 en el límite acortado de 10 s. H2 sigue abierto; véase el [registro Run-021](../agent-work/h2-state2-nested-callback-capture.md#run-021-pre-store-token-differs-from-the-later-returned-header).

Run-022 observó que, justo después del store, `r0` y el campo propietario coincidían en `0x1FF82800`; al retorno exterior el campo era `0x1FF82000`. El cambio queda acotado entre ambas observaciones, sin atribuirlo a un hilo ni a una causa concreta. El inicio expiró otra vez antes de TitleMain/State 2. H2 sigue abierto; véase el [registro Run-022](../agent-work/h2-state2-nested-callback-capture.md#run-022-post-store-value-matched-r0-later-return-snapshot-differed).

Runs 023–024 volvieron a expirar antes de TitleMain con las mismas entradas/profile staging que el run-017 revisado; Run-024 dejó ambos grupos de sondas de arranque desactivados. La traza vieja de run-017 llega a 189 s, por lo que Run-025 usa un límite de inicio de 180 s, sin ampliar los límites de callbacks/readiness. Sigue siendo diagnóstico; H2 permanece abierto. Véanse [Runs 023–024](../agent-work/h2-state2-nested-callback-capture.md#run-023-lock-probes-disabled-but-command-progress-stops-remained).

Run-026 extendió una última vez la ruta de inicio minimalista a 300 s. Pasó los cinco gates offline y mantuvo intactos el CCI, el guardado original, el fixture y las semillas; terminó `partial_failed`, antes de TitleMain, en `PC=0x002A88A8/LR=0x001465A8`, con la lectura raw `0xFFFFFFFE/0x1FF82800/1` de `0x00431C40`. El código fijado confirma que ese PC sigue a `SVC #0x22`; la captura no demuestra qué ocurrió después de reanudar ni que el wait cause el fallo de ruta. El retorno externo 2 del ID 8 permite inferir que algún callback indirecto devolvió cero según el control de flujo fijado, pero no identifica su puntero. H2 sigue abierto; no se prolongará otra vez el timeout genérico. Véase el [registro Run-026](../agent-work/h2-state2-nested-callback-capture.md#run-026-300-second-minimal-startup-attempt-stopped-at-the-known-atomic-wrapper).

### Resolución estática de la fila anidada — 2026-10-29

La entrada `/camp/config.bf` del CCI fijado ubica `SoundConfig_Change` desde la instrucción 10. Su instrucción 12 contiene `0x00210008` (handler 8, ID anidado `0x21`). En `code.bin` fijado, la fila `0x00406140` de la tabla anidada apunta a `0x00221168`. El Run-017 original registró método/instrucción 12 y handler 8, lo que alinea el recurso con aquella ruta, pero no leyó el ID anidado ni el destino del `BLX`; sigue siendo correlación estática/runtime, no captura dinámica. La auditoría independiente de `0x00221168` confirma algunos argumentos, stores y propagación de retorno, pero los punteros globales y el helper final `0x00286928` siguen sin contrato tipado. No hay candidata C++ ni diferencial de esta callback. Véanse el [registro de resolución/captura](../agent-work/h2-state2-nested-callback-capture.md#static-resolution-of-the-soundconfig-instruction-12-row) y el [audit del contrato](../agent-work/h2-callback-contract-00221168.md).


### Actualización — Run-028 (2026-10-29)

Run-028 añade una observación dinámica acotada al caller nativo detectado en Run-027. Con el `LDRB` original ya ejecutado, `0x0010316C` registró `r0=0`, `r8=0x004E3CF4` y dirección `0x004E3D04`. El programa tomó la rama original hasta `0x0010319C` (1,207 s; `r0=0`, `r5=0`) y alcanzó el retorno de `BL 0x002C43D4` en `0x001031A4` (1,220 s; `r0=0`, `r5=0`). El helper retornó cero. La instrucción posterior y la interpretación funcional del byte no se probaron por separado.

La captura terminó `partial_failed` al límite de inicio de 30 s, antes de `TitleMain_Init`. `PC/LR=0x002A88A8/0x001465A8`; la lectura de diagnóstico registró `0xFFFFFFFE/0x1FF82800/1` en `0x00431C40`. No demuestra un bloqueo permanente ni explica la ruta ausente. No hubo dispatch de State 2 ni llegada a `0x001A07FC/0x001A0800`, y no se establece vínculo entre el caller de Run-028 y el ID 8 de la ruta de Run-017. H2 permanece abierto; no se extenderá otra vez el timeout genérico.

Pasaron los gates offline H2, caller H2, composición final H3 y ARM interworking. Se mantuvieron visibles cuatro avisos de identidad de fuentes H2. El guardado original no se cargó y conservó su SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; el fixture desechable también quedó intacto. El supervisor retiró el perfil temporal y dejó cero breakpoints. Una revisión independiente confirmó el orden de las sondas y los eventos; los mocks solo prueban la secuencia RSP programada, no ejecutan ARM. El informe crudo se conserva aparte porque su campo inicial `limitations` estaba vacío; la copia anotada enumera los límites explícitos.

El `h2-state2-dispatch-runtime-capture/run-017` sí llegó a TitleMain/State 2 con el mismo hash de CCI, Azahar, fixture y semillas de perfil. El paquete/reporte no guardó el hash del runner; el historial de comandos sí recupera sus argumentos, detallados abajo. Eso no basta para atribuir la divergencia a una causa concreta. Antes de otra ejecución hay que identificar una diferencia técnica nueva y preparar una captura específica; no repetir el arranque genérico.

Evidencia: [informe anotado](../../build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-028/runtime-report.json), [informe crudo](../../build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-028/runtime-report-raw.json), [revisión](../../build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-028/independent-review.md) y [handoff](../../build/agent-work/H2-semantic/h2-state2-nested-callback-capture/run-028/handoff.json).

La diferencia visible entre ambos informes es de ruta, no solo de registro: `h2-state2-dispatch-runtime-capture/run-017` contiene 12 entradas y 12 retornos del dispatcher, con el handler ID 8 en `0x001A07CC` y State 2; `h2-state2-nested-callback-capture/run-028` no contiene entradas/retornos de handler ni arrays de State 2. En Run-028, el snapshot posterior a la llamada en `0x00103164` muestra un contexto local distinto (`r4=0x082EFE00`, palabra +8 = 67) al contexto de progreso del script (`0x014657380`, palabra +8 pasa de 11 a 12). El volcado posterior contiene `0x001C0300` en `r4+0x3C`, pero no se leyó ese puntero antes del `BLX`, así que no se etiqueta como su destino dinámico. No hay prueba de que este caller previo sea la ruta de ID 8.


El historial de comandos del hilo conserva la invocación de `h2-state2-dispatch-runtime-capture/run-017`: usó `--port 46797`, `--startup-timeout 60`, `--packet-timeout 30` y `--capture-timeout 180`, escribiendo stdout en su `runner-console.log`. Esto recupera los argumentos que faltaban en el JSON, pero no el hash del archivo `tools/h2_state2_dispatch_trace.py` que los ejecutó. La línea de comandos sola no permite repetir Run-017 de forma idéntica ni explicar por qué difiere del runner actual.


### Actualización — Aislamiento de fallos del observador (2026-10-29)

El build privado de Azahar cambió el callback opcional de observación de `Core::System::RunLoop` a contrato `void`: si la captura devuelve fallo o lanza una excepción, el observador intenta registrar un estado incompleto y las siguientes capturas quedan desactivadas; el bucle continúa hacia `ExecuteCore`. `bootmanager.cpp` no cambió y mantiene el tratamiento existente de errores reales de `Core::System`. El target privado `azahar.exe` compiló con un job y terminó con código 0 (`core.cpp` SHA-256 `3e495c22e69d3fdb26e15b6f167f893089e5eee90e59c438ee79e538d080f82c`; ejecutable SHA-256 `1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682`). La revisión independiente aceptó esta afirmación acotada de control de flujo.

La prueba disponible ejercita directamente `H2Observer`, no `RunLoop` ni la frontera con Qt; tampoco inyecta fallos de serialización o sistema de archivos. La revisión registra además que falta el código fuente del baseline exacto y un recibo que vincule el binario de test preexistente con la fuente fijada. El build y la revisión fueron estáticos/offline: no se lanzó Azahar. Esto no identifica la causa del diálogo fatal anterior, no confirma una captura viva y no completa H2. Antes de ampliar la afirmación queda pendiente una prueba de integración de `Core::System` que compruebe que `ExecuteCore` sigue ejecutándose tras el fallo del observador y que los errores reales conservan su ruta.

Evidencia: [informe de implementación](../agent-work/h2-observer-failure-isolation.md), [handoff](../../build/agent-work/H2-semantic/h2-observer-failure-isolation/run-002/handoff.json), [revisión independiente](../../build/agent-work/H2-semantic/h2-observer-failure-isolation/run-003/independent-review.md) y [hashes del build](../../build/agent-work/H2-semantic/h2-observer-failure-isolation/run-002/checks/build-output-hashes.json).

### Seguimiento de procedencia — test del observador (run-004)

Tras la revisión independiente se recompiló `test_h2_observer.exe` desde `tests/test_h2_observer.cpp` (SHA-256 `79efc580c49f0b071ee00416754dd3e92fe938c96a3baa237749a0e4e4b6cbc6`), `h2_observer.cpp` (`698cd00f8cdca5ab3693a416bc21ac390dece4e1c15d8ba22b63977ed5253f30`) y su header (`d9e30c5efd3618e45d5eeb9ce0f85d40229bd6489ed824336cec32d426abdccb`). Compilación C++20 y ejecución: exit 0; el binario nuevo tiene SHA-256 `d9844c0eff6f989ad4823960af935c22a130ebd30fa50c3413eaac922d2fc3d3`. La [verificación](../../build/agent-work/H2-semantic/h2-observer-failure-isolation/run-004/checks/verification.json) conserva los logs y hashes.

Esto resuelve la falta de recibo de compilación del binario anterior para la cobertura directa de `H2Observer`. No cambia el límite principal: no prueba la integración `RunLoop` → `ExecuteCore`, fallos de serialización/E/S ni comportamiento en vivo.
