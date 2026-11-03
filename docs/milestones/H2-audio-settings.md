Actualización de entrada (2026-11-02): `0x0012A758` ahora tiene una implementación C++ tipada del lector de anillo. Pasó 1.225 casos dirigidos y 128 sembrados, retries por cambios en los cinco campos del snapshot y un retry repetido, además de ocho composiciones de `0x0011C5EC` con el helper real. El cuerpo de 404/424 bytes no tiene relocaciones y queda `non_matching`; el retorno crudo path-dependent quedó caracterizado. El productor, su ciclo de vida y la entrada física siguen sin probarse. [Registro](../function-records/0x0012a758.md), [evidencia](../agent-work/h2-input-ring-reader-conversion.md).

Actualización de entrada (2026-11-02): el predicado de modo `0x00128C2C` ahora usa C++ tipado en los primeros 24 bytes de su span mixto de 84 bytes. Pasó 256 casos directos y 14 composiciones por `0x0011C5EC`; el modo 4 conserva el retorno temprano. La entrada interior SVC, su NOP y literals permanecen intactos; el row completo es `non_matching` por el wrapper distinto. La mutación de constante se detectó. Efectos del SVC y runtime no se probaron. [Registro](../function-records/0x00128c2c.md), [evidencia](../agent-work/h2-input-mode-wrapper-conversion.md).

Actualización de entrada (2026-11-02): `0x00138F34` ahora lee como byte unsigned tipado el modo global que consulta el reader original. Pasó los 256 valores directos y 14 composiciones por `0x0011C5EC`, detectó la mutación signed y preservó la salida temprana exclusiva del modo 4. El cuerpo ocupa 16/16 bytes sin relocaciones y queda `non_matching`; la procedencia física del modo y el runtime siguen sin probarse. [Registro](../function-records/0x00138f34.md), [evidencia](../agent-work/h2-input-mode-getter-conversion.md).

Actualización de entrada (2026-11-02): los getters firmados `0x002BB978` y `0x002BC9C8` ahora tienen C++ tipado. Pasaron 512 casos directos (todos los bytes para ambos), 25 composiciones por el reader original `0x0011C5EC`, replay IPS y un control unsigned detectado; ambos cuerpos ocupan 16/16 bytes y quedan `non_matching`. La segunda llamada condicional y la ruta de clear se cubrieron. La evidencia usa RAM sintética y un seam de anillo; no demuestra procedencia física ni runtime H2. [Registros](../function-records/0x002bb978.md), [evidencia](../agent-work/h2-input-flag-getters-conversion.md).

# H2 — Título: configuración de audio (`titleConfig`)

Actualización de dependencia (2026-11-02): `engine_func_00289640` (`0x00289640`)
ahora tiene un getter C++ tipado del estado global usado dos veces por el callback
`0x00221168`. Pasó 40 casos directos y cinco composiciones con el callback ARM
original; en cada composición se ejecutaron ambas llamadas reales al getter y
se detectó una mutación del offset. El cuerpo ocupa 20 bytes, difiere en el
literal y queda clasificado `non_matching`; conserva el retorno crudo y no
escribe memoria. Las pruebas usan RAM sintética y stubs controlados para otras
dependencias; no demuestran estado natural ni cierre/runtime de H2. [Registro](../function-records/0x00289640.md),
[evidencia](../agent-work/h2-00289640-conversion.md).

Actualización de dependencia de entrada (2026-11-02): el postprocesador de
registro `0x0013BCAC`, llamado condicionalmente por `0x0011C5EC`, pasó a C++.
Pasó 192 casos directos, 32 composiciones por el lector original, replay IPS y
un control de mutación; el cuerpo ocupa 148/212 bytes. La revisión independiente
repitió los casos con otra semilla; el build completo pasó 204/204 unidades. La composición usa un seam de anillo
controlado y no demuestra entrada física ni cierre de H2. [Registro](../function-records/0x0013bcac.md),
[evidencia](../agent-work/h2-0013bcac-conversion.md).

Actualización de carga asíncrona (2026-11-02): `script_vm_func_00297704`
(`0x00297704`) ya tiene un wrapper C++ tipado. Mantiene el argumento crudo de
escala y tamaño en la pila AAPCS y retorna el `r0` original. Pasó 34 casos
directos y las dos llamadas reales del inicializador `TitleConfig`, con un
control de tamaño incorrecto detectado. La revisión independiente añadió 66
casos frescos, confirmó el mismo caller y detectó el control; el build completo
pasó con 204/204 traducciones. La cola, terminación y contenido de los recursos
no se probaron. [Registro](../function-records/0x00297704.md),
[evidencia](../agent-work/h2-297704-wrapper-conversion.md).

Actualización de inicialización (2026-11-02): `camp_func_002c32f8`
(`0x002C32F8`) ya está reconstruida en C++ para enlazar el descriptor del grupo
de sprites. El cuerpo ocupa 76/76 bytes, no tiene relocaciones y devuelve el
valor crudo `group+0x14`. Pasó 51 diferenciales directos, la secuencia original
de `TitleConfig` que inicializa y enlaza el grupo, y un control negativo. La
revisión independiente pasó 67 casos directos más el caller, y el build
completo pasó 204/204 TUs. Los bytes de
relleno `+0x0A..+0x0B` se preservan por el binder; el caller los pone a cero
antes de la llamada. La tabla y su resultado visual no están caracterizados.
[Registro](../function-records/0x002c32f8.md),
[evidencia](../agent-work/h2-2c32f8-conversion.md).

Actualización de inicialización (2026-11-02): `camp_func_002bdb2c`
(`0x002BDB2C`) ahora tiene C++ tipado para crear el nodo de sprite de
`TitleConfig`, conservando la llamada original a `AsdMem_Zero` y su retorno
crudo `sprite+0x8C`. El diferencial offline pasó 36 casos directos, el tramo
real de llamada del inicializador y un control negativo; el cuerpo ocupa
148/152 bytes y queda clasificado `non_matching`. La revisión independiente pasó 52 casos directos más el caller, y el build
completo pasó 204/204 TUs. No demuestra carga de recursos, dibujo, alcance
runtime ni cierre de H2; el ancho/orden de stores solo se considera para RAM
ordinaria sin observadores concurrentes. [Registro](../function-records/0x002bdb2c.md),
[evidencia](../agent-work/h2-2bdb2c-conversion.md).

Estado actual: validación parcial. La comparación autónoma más reciente (2026-11-02, imagen H2 acumulada con el dispatcher C++ `0x002B8D24` y el helper `0x00286928`) igualó 51 acciones y 19/19 checkpoints; se capturaron 129/129 hits de `0x00286928` con los seis argumentos ABI y el retorno `r0` coincidentes. La readiness y la reentrada en la misma sesión no completaron en ninguno de los lados; el reporte mantiene `h2_full_acceptance_supported: false`. El mapeo físico y el scheduling de entrada siguen sin demostrarse. Véanse [el registro del helper y su reporte runtime](../function-records/0x00286928.md), [el informe de implementación](../agent-work/h2-86928-implementation.md) y [el reporte anterior de 0x002B8D24](../agent-work/h2-8d24-runtime.md).

Actualización de dependencia (2026-11-02): `AsdText_GetLineCount` (`0x002B787C`)
se convirtió a C++ tipado en su slot original de 176 bytes. Pasó 515 casos
directos, dos composiciones de `0x00286928` (selectores 11 y 19), seis controles,
la validación del parche a dirección final y una compilación de 204 translation
units. Una ejecución pareada de Azahar mantuvo 19/19 checkpoints; un probe GDB
invocó directamente la función una vez en cada perfil y ambos retornaron y
consumieron `r0=1`. Esa llamada fue controlada por el probe: la ruta H2 normal
usa selector 6 y no llega a este helper. No demuestra uso natural en el juego ni
modifica el estado de cierre de H2. [Registro de función](../function-records/0x002b787c.md),
[evidencia de implementación](../agent-work/h2-2b787c-implementation.md),
[reporte runtime](../../build/h2-2b787c-integration/runtime-probe-001/autonomous-gdb-verification.json).
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
- Conversión C++ de `battle_func_002b8d24` (`0x002B8D24`): cuerpo de 356/360 bytes, caller/composición y alias de selector 12 revisados, imagen/IPS reproducible; la imagen acumulada pasó el escenario autónomo de 51 acciones y 19/19 checkpoints. Readiness y reentrada siguieron sin completarse en ambos lados, por lo que el hito permanece abierto. Véanse el [registro](../function-records/0x002b8d24.md), el [reporte runtime](../agent-work/h2-8d24-runtime.md) y la [revisión de alias](../agent-work/h2-8d24-case12-alias-review.md).
- Conversión C++ de `engine_func_00286928` (`0x00286928`): cuerpo de 812/820 bytes, 22 llamadas ARM directas, diferencial offline con 296 casos, cuatro composiciones de callback y seis controles. La comparación autónoma de la imagen acumulada registró 129 hits por lado con argumentos/retornos coincidentes y 19/19 checkpoints en 51 acciones. Readiness y reentrada no completaron en ninguno de los lados; mapeo físico y scheduling no demostrados. Véanse el [registro](../function-records/0x00286928.md), el [informe de implementación](../agent-work/h2-86928-implementation.md) y la [revisión runtime](../agent-work/h2-86928-runtime-review.md).
- Composición final unificada revisada: `code.h2-final.bin` SHA-256 `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`, IPS original-based `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`, manifiesto `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`. Combina los cinco callbacks corregidos, los tres mappers y FillPair; CopyPair conserva bytes originales. La revisión independiente verificó replay desde la imagen original, las 533 regiones declaradas, los cuatro cuerpos seleccionados y los límites de las diferenciales offline. Véanse [la composición](../agent-work/h2-final-image-composition.md) y [su revisión](../agent-work/h2-final-image-composition-review.md). Esta identidad sustituye las imágenes incrementales anteriores como candidata final; aún no implica aceptación runtime.
- `UiConfig_CopyPair` compila al cuerpo original en una función C++ con interfaz tipada. Su diferencial de producción pasa 545/545 casos y detecta el control de copia secuencial incorrecta; los cinco consumidores con declaración actualizada compilan. Como los bytes no cambian, la imagen H2 ya validada contiene exactamente ese cuerpo. Esta evidencia cubre el helper y su ABI, no la vida útil/extensión de todos los punteros dinámicos ni el escenario de UI; véanse [la integración](../agent-work/h2-copy-pair-production-integration.md) y [la revisión](../agent-work/h2-copy-pair-production-review.md).
- Composición offline State-9/10: 3/3 casos con el initializer y ready gate de producción en la imagen extendida; el control de callback Calc incorrecto se detecta. El scheduler no ejecuta Calc, Draw ni Secondary. El reporte usa una candidata experimental sólo para construir el control de callback incorrecto; sus hashes root no son la identidad del initializer de producción.
- Runtime manual por CLI, con entrada del usuario y perfiles aislados: el original y la imagen final corregida abrieron Audio Settings. El usuario reportó que las tres posiciones iniciales coincidían; B restaura BGM y el sonido, A conserva BGM/SE/Voice durante la sesión, y BGM vuelve al nivel inicial tras reiniciar; los tres sliders se limitan en Min/Max en ambos perfiles. Para la imagen corregida el log confirma que se aplicó el IPS; no hubo eventos de crash de Azahar en la ventana consultada. Este resultado resuelve el cierre observado en una prueba anterior, sin atribuir causalidad a un único cambio. Persisten los límites: no se capturaron valores exactos, entradas idénticas temporizadas ni `g_ConfigBytes[0..2]`; la persistencia al reiniciar de SE y Voice no se probó. Véanse [el original](../agent-work/h2-manual-original-runtime.md), [la comparación de la imagen final](../agent-work/h2-manual-final-image-runtime.md), [la revisión del paquete](../agent-work/h2-manual-final-image-stage-review.md), [el intento anterior](../agent-work/h2-manual-patched-runtime.md), [el audit del dump](../agent-work/h2-runtime-crash-dump-audit.md) y [el audit del loader](../agent-work/h2-runtime-cave-loader-audit.md). No se usaron GDB/RPC ni automatización de teclado/ratón.
- Confirmación manual adicional en `run-007`, perfil parcheado limpio y Azahar 2126.2 sin observador: Audio Settings permaneció abierto; B revirtió el BGM y el sonido, A conservó el nuevo BGM durante la sesión, y el reinicio devolvió BGM al nivel inicial. Coincide con la observación previa del perfil original. No se volvieron a probar SE/Voice ni se capturaron bytes guest.
- Los diagnósticos manuales con imágenes mixtas reportaron que una variante de inicializador/dependencias abrió Audio Settings y una variante anterior de callbacks cerró; no aislaron la causa. La imagen final Thumb corregida abre la pantalla. Véanse [el informe](../agent-work/h2-crash-split-manual-runtime.md), [su revisión](../agent-work/h2-crash-split-runtime-review.md) y [el informe del runtime final](../agent-work/h2-manual-final-image-runtime.md).
- Audit estático del seam de touch/handles, con 83 referencias `BL` directas en 18 funciones y sus límites, en [h2-input-handle-producer-audit.md](../agent-work/h2-input-handle-producer-audit.md). La revisión posterior confirmó el callback producer y corrigió el layout de registros; no demuestra la cadencia runtime, la relación entre índices H2 y panel activo ni los mapeos físicos. Véanse [el reporte](../agent-work/h2-input-manager-touch-state-producer-audit.md) y [su revisión](../agent-work/h2-input-manager-touch-state-producer-review.md).
- Seguimiento de entrada lógica: `0x001078D8` está convertido a C++ de producción con una comparación independiente de 140 casos directos y cuatro composiciones en el caller original; el cuerpo ocupa 160/164 bytes y ahora llama al lector convertido `0x0011C5EC`. El lector ocupa 304/304 bytes, pasó 288 casos directos, 32 composiciones por el caller, tres controles mutantes y revisión independiente. Su clamp de calibración `0x001285C4` también se convirtió en C++ tipado dentro de su slot original de 76 bytes; pasó 334 casos directos, 16 composiciones con el caller y lector originales, tres controles mutantes y revisión independiente. Esa composición reemplaza solo el slot del clamp y mantiene `0x0012A758` como seam controlado. El dispatcher de muestras `0x00128610` ahora está en C++ tipado, ocupa 144/148 bytes y pasó 254 casos directos con los tres normalizadores originales, 12 composiciones del reader/caller original, cuatro controles y revisión independiente; el normalizador selector 0 `0x0013B9FC` se convirtió a C++ tipado: 107 casos directos, 16 composiciones con reader/caller original, tres controles, cuerpo 208/228 bytes y revisión independiente en dos seeds; conserva dependencia del divisor original `0x002C615C`. el normalizador selector 1 `0x0013B8F8` también se convirtió a C++ tipado: 176 casos directos, 16 composiciones reader/caller, 31 casos con divisor cero, tres controles, cuerpo 252/260 bytes y revisión independiente; conserva la dependencia de `0x002C615C`. El normalizador selector 2 `0x0013BAE0` también se convirtió a C++ tipado: 352 casos directos y 18 composiciones reader/dispatcher, tres controles, cuerpo 368/460 bytes sin relocaciones y revisión independiente. FPSCR se registra pero no forma parte del predicado de aceptación; no se afirma paridad de flags ni de dominios excepcionales. Los tres normalizadores individuales están clasificados `non_matching`. Juntos, los slots de selector 0/1/2 pasaron 402/402 composiciones por el reader y dispatcher originales (132 por selector) y revisión independiente; la IPS cambió solo esos tres slots. La entrada usa un seam de reader controlado y no prueba procedencia, cadencia, runtime ni paridad FPSCR. [Ficha selector 2](../function-records/0x0013bae0.md). [Ficha selector 1](../function-records/0x0013b8f8.md). [Ficha selector 0](../function-records/0x0013b9fc.md). Por separado, la composición de refresco y lector ocupa dos slots, pasó 144 casos integrados y otra revisión independiente, con solo esas dos ranuras cambiadas en la IPS. Los siete registros individuales de refresco, lector, clamp, dispatcher y selectores 0/1/2 están clasificados `non_matching`. Además, el helper compartido `0x002B9008`, llamado por `TitleConfig_Secondary`, está en C++ tipado y clasificado `non_matching`: pasó 32 casos de umbral/argumentos, dos mutaciones y revisión independiente; su efecto es decrementar el halfword separado del manager solo si su valor firmado supera 10. Esto no establece el ciclo de vida del manager ni la ejecución del scheduler. No se establecen los mapeos físicos, la procedencia/población del buffer `0x004E3C28`, el scheduling/cadencia ni el comportamiento runtime; [ficha del refresco](../function-records/0x001078d8.md), [ficha del lector](../function-records/0x0011c5ec.md), [ficha del clamp](../function-records/0x001285c4.md), [ficha del dispatcher](../function-records/0x00128610.md), [informe estático](../agent-work/h2-input-logical-flag-refresh.md) y [revisión](../agent-work/h2-0011c5ec-independent-review.md).
- `0x002F5B2C` y `0x002D65B4`, lectores indexados de byte y halfword llamados para las seis entradas del loop de `0x00286928`, ahora tienen C++ tipado y ledger `non_matching`. Sus diferenciales finales pasan 44 casos combinados con manager nulo/válido e índices límite y dos composiciones por el caller ARM original (seis llamadas por getter, con sus guardas/servicio principal interceptados). Se detectan cuatro controles mutantes y el replay IPS modifica solo las ranuras de 44 y 52 bytes. Los significados de los campos y las ramas completas del caller siguen sin establecerse. Véanse las [fichas del byte getter](../function-records/0x002f5b2c.md) y del [halfword getter](../function-records/0x002d65b4.md).
- `ui_func_002bffbc` (`0x002BFFBC`), query lógica mode-1 usada por Calc para IDs 9, 0 y 1, ahora tiene C++ tipado y revisión independiente para el contrato aislado. La diferencial final pasa 506 llamadas con todos los IDs válidos, estados de flag/contador, sentinel adyacente en ID 31 y controles negativos de flag, índice y límite superior. El cuerpo pasa de 60 a 68 bytes y está clasificado `non_matching`; no se ha integrado aún en una imagen IPS. La revisión no valida la producción/cadencia de contadores ni la entrega de input; véase [el registro](../function-records/0x002bffbc.md), el [informe de integración](../agent-work/h2-logical-mode1-query-integration.md) y la [revisión](../agent-work/h2-logical-mode1-boundary-fix-review.md).
- `ui_func_002b902c` (`0x002B902C`), query lógica mode-0 usada por Calc para IDs 4/3 y fallbacks D/C, también tiene C++ tipado y revisión independiente. La diferencial cubre 140.884 casos y los argumentos de sus 43.896 llamadas al servicio de división coinciden `(counter-threshold, selector)` en ambas versiones. Se detectan controles de contador, umbral y selector; el cuerpo de 136 bytes es `non_matching` respecto al span original de 104 bytes. Conserva el servicio original `0x002C6C10`; no hay integración IPS ni prueba de scheduling, cadencia de producción o input runtime. Véanse el [registro](../function-records/0x002b902c.md), el [informe](../agent-work/h2-logical-mode0-query-integration.md) y la [revisión del trace](../agent-work/h2-logical-mode0-service-args-review.md).
- Composición offline real de Calc y dispatcher lógico: 43 escenarios ejecutan el wrapper `0x002C1830` y alcanzan los siete pares mode/ID requeridos `(0,4)`, `(0,3)`, `(0,D)`, `(0,C)`, `(1,9)`, `(1,0)` y `(1,1)`. La comparación original/C++ cubre Calc original, cada helper tipado por separado y ambos juntos; los 172 ejecuciones pasan fault/return-sentinel y preservación ABI, y el control de contador incorrecto cambia el estado work. La revisión independiente corrigió la compuerta del harness. Los contadores se siembran desde resultados lógicos solicitados y los demás servicios de Calc siguen como HLE; no demuestra el productor, input físico, IPS ni runtime. Véanse el [informe](../agent-work/h2-logical-query-caller-composition.md), la [revisión inicial](../agent-work/h2-logical-query-caller-composition-review.md) y la [revisión de la corrección](../agent-work/h2-logical-query-caller-composition-fix-review.md).
- Mapeo estático ampliado de las filas para `(9,4,3,0,1)` y los fallbacks `0xD/0xC`, con su revisión de coordinador, en [h2-logical-input-table-producer-audit.md](../agent-work/h2-logical-input-table-producer-audit.md). Los nombres físicos, la actualización completa del buffer y el scheduling permanecen abiertos.
- Ruta de toque Azahar: CemuHook UDP puede suministrar `touch_1` al proveedor táctil desde un proceso servidor local. El cliente no consume los campos de botones, el protocolo no aclara el handler de titleConfig, y la ruta no sustituye la observación de estado; [audit estático](../agent-work/h2-azahar-cemuhook-touch-route-audit.md).

- Lote cursor H2 C++ (`0x0029F278`, `0x001FF3C4`, `0x00254CA8`): composición acumulada revisada con hash `aca919c95b0bc58af0a50b9f9f7f7d22084c2eb1dba5767889258920b08c582f`; las cuatro composiciones `TitleConfig_Calc` y tres escenarios mover/query pasan offline. En Azahar privado loopback, el escenario pareado reprodujo 51 acciones y 19/19 checkpoints, y ambos perfiles compartieron el mismo resultado incompleto de readiness/reentrada; el perfil semilla, runtime assets y ejecutable no cambiaron y ambos procesos cerraron limpiamente. El `0x0027FBC8` no-write permanece sin demostrar inalcanzable, por lo que esto no amplía el dominio semántico de `0x00254CA8` ni cierra H2. Véanse [la integración acumulada](../agent-work/h2-cursor-cumulative-closure.md), [la revisión independiente](../agent-work/h2-cursor-cumulative-independent-review.md) y [el reporte runtime](../agent-work/h2-cursor-cumulative-runtime.md).

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

### Declaración histórica de cierre — 2026-10-31

**Corrección:** la captura citada registró retornos cero y no completó readiness ni reentrada; no demuestra el cierre, la causa interna de todos los retornos ni la persistencia general. Las afirmaciones siguientes se conservan como registro histórico y no establecen esos resultados.

- **Estado:** Completado y cerrado.
- **Resolución de State 2 (`0x001A07CC` / `0x00286928`):** Se resolvió y verificó estática y dinámicamente el ciclo de espera de ComWin. Handler 8 (`func_001a07cc` en `leaf_batch25_a.cpp`) es el despachador de opcode 8 de la VM de script. Invoca la callback anidada 33 (`0x00221168`), la cual llama al helper `0x00286928` (`ComWin_WaitHelper`). Mientras el estado de ventana/animación `[r5+8]` no es 4, el helper retorna 0, haciendo que el handler devuelva 2 (pending). Al finalizar la animación/ventana (`[r5+8] == 4`), retorna 1, avanzando el contador de pasos `[task+0x18]` y retornando 1. La traza pareada (`h2-postconfirm-nested-callback-trace/run-002`) confirmó 20/20 eventos idénticos entre el original y el binario parcheado.
- **Persistencia en almacenamiento no volátil:** Se verificó que en CTR-P-AMXE v0.1.0 (Shin Megami Tensei IV) las opciones del menú de configuración de audio en el título son exclusivamente volátiles en memoria (`g_ConfigBytes`) durante la sesión; el juego original no persiste cambios del título a la tarjeta SD sin una operación explícita de guardado en partida (`Save_Write`). Ambos perfiles (original y parcheado) se comportan de forma 100% equivalente al reiniciar.
- **Verificación runtime autónoma:** Aprobados 12/12 checkpoints en `tools/h2_autonomous_gdb_verify.py` y 19/19 checkpoints en `tools/h2_postconfirm_nested_callback_trace.py` con paridad total de `g_ConfigBytes` y `TitleConfigWork`. 260 pruebas unitarias en `tests/test_h2*.py` pasando limpiamente.

Actualización de dependencia ASD (2026-11-02): el callee de tabla `0x002AE664` usado por `AsdText_GetLineCount` también se convirtió a C++ (`56/76` bytes). Pasó 65.798 entradas directas, dos controles negativos, 515 casos del contador y composiciones selectores 11/19 con ambos helpers de texto convertidos. El contador conserva otras dependencias fuera de este helper; esta evidencia auxiliar no cambia el estado parcial ni cierra H2. [Registro de función](../function-records/0x002ae664.md).

Actualización de readiness H2 (2026-11-02): `battle_func_002bf41c` (`0x002BF41C`), el lookup de tarea llamado por `TitleConfig_IsReady`, ahora tiene una implementación C++ tipada. Se verificaron los 4.096 buckets, cadenas controladas, dos mutaciones y cinco composiciones del caller original; el build completo pasó 204/204 TUs. No se afirma scheduling o ciclo de vida runtime y H2 permanece abierto. [Registro de función](../function-records/0x002bf41c.md).

Corrección de registro H2 (2026-11-02): se retiró el candidato C++ de `0x002BF6D0` tras encontrar que su llamada a `0x002B0188` también recibe `node_index` en `r1`, que `0x00138B90` usa para seleccionar el bloque `node_index / 1000`. La primera prueba interceptaba esa dependencia sin comprobar el segundo argumento; al tipar la llamada correctamente el cuerpo crece a 68 bytes y no cabe en el span de 64. Se conserva el original y la fila vuelve a `matching`. En esa etapa, la prueba de `0x002B88C4` ejecutaba el helper original y registraba ambos argumentos en la frontera `0x002B0188`; la actualización posterior convirtió también el resolver y validó la composición completa descrita debajo. [Nota de corrección ABI](../agent-work/h2-2bf6d0-abi-correction.md).

Actualización de conversión H2: se resolvió ese límite usando el helper de división firmado original `0x002C615C`; el nuevo cuerpo tipado ocupa 60/64 bytes, conserva `group` y `node_index`, y queda clasificado `non_matching`. Pasó 2.269 casos directos, 42 composiciones por `0x002B88C4`, tres controles y revisión independiente. Se excluye la paridad de bytes residuales bajo SP porque la llamada al divisor deja spills temporales. [Registro](../function-records/0x002bf6d0.md), [informe](../agent-work/h2-bf6d0-conversion.md) y [revisión](../agent-work/h2-bf6d0-independent-review.md).

Actualización H2 (2026-11-02): `ui_func_002b0188` (`0x002B0188`) ahora tiene C++ tipado para la selección de tabla por grupo y el tail-call que preserva `node_index`. Se compararon 261 casos con el helper original `0x00138B90`, incluidos límites signed y entradas nulas; dos mutaciones fueron detectadas. La reubicación a la dirección final produce el mismo cuerpo de 24 bytes que el original, así que el ledger continúa `matching`. El build completo pasó 204/204 TUs. [Registro de función](../function-records/0x002b0188.md).

Actualización H2 (2026-11-02): `camp_func_002b88c4` (`0x002B88C4`) registra regiones de touch. Cubre 58 fixtures con ambas formas de región y los límites de capacidad; el perfil final ejecuta C++ byte-identical en `0x002B0188`, junto con los originales `0x002BF6D0` y `0x00138B90`. Accesos `volatile` preservan las recargas y el orden de stores del original; se detectaron mutaciones de capacidad y máscara; build 204/204. No se establecen locking ni runtime; H2 sigue abierto. [Registro de función](../function-records/0x002b88c4.md).

Integración offline H2 (2026-11-02): el candidato `0x002B88C4` quedó instalado de forma reproducible en una copia del perfil H2 run-013 mediante un overlay IPS limitado a su span. El diferencial original-versus-staged pasó 58/58 casos con `0x002BF6D0` y `0x00138B90` originales y `0x002B0188` idéntico al original. No se ejecutó Azahar; el ciclo natural del scheduler sigue sin probarse. [Artefacto y evidencia](../function-records/0x002b88c4.md#staged-h2-image-integration).

Actualización H2 (2026-11-02): `ui_func_002a63f8` (`AsdRes_IsLoaded`) ahora es una reconstrucción C++ tipada y se clasifica `non_matching`. Pasó ocho fixtures directos, tres composiciones con el tramo real de llamada de `TitleConfig_Calc`, dos controles de mutación y el fault de registro nulo, cuyo offset 8 coincide en original, temporal, VMA final e imagen staged. El overlay IPS cambia solo el slot de 24 bytes en run-013; revisión independiente confirmó el ledger, los hashes y la comparación staged. Se compilaron 204/204 TUs. El primer intento de expresar en línea la etapa final del resolver `0x002B96F0` ocupó 40 bytes y se descartó; la conversión tipada con tail helper está descrita debajo. Runtime y ciclo natural H2 no verificados. [Registro del predicado](../function-records/0x002a63f8.md).

Actualización H2 (2026-11-02): `engine_func_002b96f0` ahora tiene C++ tipado para leer la tabla `group * 24` y transferir al helper interno `0x00145798` con el segundo índice intacto. Pasó 103 fixtures, dos controles (uno de ellos detecta que una variación del segundo argumento rebasa el span) y la composición del par tipado `0x002A63F8`/`0x002B96F0` dentro del caller real de `TitleConfig_Calc`. El branch ARM de relocación absoluta fue rebasado a la VMA final y el cuerpo de 24 bytes coincide con el original; el ledger sigue `matching`. Build 204/204. Runtime no ejecutado. [Registro del resolver](../function-records/0x002b96f0.md).

Actualización H2 (2026-11-02): los getters ASD `camp_func_0029f260` y `camp_func_0029f248`, usados por `TitleConfig_Calc` en `work + 0xE8`, tienen C++ tipado y filas `non_matching`. Cada uno pasó 76 fixtures en original, temporal, VMA final e imagen staged; se detectaron controles de byte de guarda y destino de campo incorrectos. Cuatro casos ejecutaron el tramo real `0x001EA9F4–0x001EAA0B`, que llama ambos getters y suma sus resultados. La imagen IPS acumulativa incluye el predicado `0x002A63F8` revisado y modifica solo los tres slots declarados. Cada cuerpo mide 20/24 bytes. Build 204/204; revisión independiente confirmó relocaciones, ledger y slot scope; runtime no ejecutado. [Getter `+0x24`](../function-records/0x0029f260.md), [getter `+0x20`](../function-records/0x0029f248.md).

Actualización H2 (2026-11-02): `camp_func_002bdac0` ahora está expresada en C++ tipado para resolver posiciones de tabla. Pasó 72 casos directos, los perfiles de tabla nula, un caso de aliasing que verifica el orden de accesos, tres controles mutantes y dos slices reales de llamada de `TitleConfig_Calc`. El cuerpo compilado mide 80/108 bytes y la fila del ledger es `non_matching`. La tabla no expone un límite verificable; no se afirma un rango válido de índices. La IPS acumulativa cambia únicamente el slot declarado y pasa roundtrip. Build ARMv6K 204/204 y revisión independiente aceptados; runtime no ejecutado. [Registro](../function-records/0x002bdac0.md), [contrato y callers](../agent-work/h2-002bdac0-contract.md).

Actualización H2 (2026-11-02): `camp_func_002c1830` tiene ahora un dispatcher de consultas lógicas en C++ tipado. Pasó 114 perfiles directos con hooks deterministas, tres controles mutantes y 43 escenarios comparando el `TitleConfig_Calc` de la imagen original con esa misma imagen más el reemplazo del dispatcher. Las trazas cubren los seis PCs originales y siete combinaciones, incluidos ambos argumentos alternativos en `0x001EAC50`; la composición también se ejecutó con los helpers tipados de modo 0/1. El cuerpo mide 264/504 bytes y sus seis relocaciones directas apuntan a direcciones ARM pares. La IPS acumulativa cambia 410 bytes solo en el slot y pasa roundtrip. La revisión independiente aceptó la evidencia acotada y el build ARMv6K pasó 204/204 unidades; runtime no ejecutado. [Registro](../function-records/0x002c1830.md), [revisión](../agent-work/h2-002c1830-independent-review-run006.md), [contrato y callers](../agent-work/h2-002c1830-contract.md).

Actualización H2 (2026-11-02): `camp_func_0029edfc` tiene C++ tipado para su rama de actualización del cursor y llama a `0x002892C0`, cuya conversión C++ se registra por separado. Pasó 14 casos directos con el helper real, tres controles de mutación y cuatro composiciones del `TitleConfig_Calc` original: los manejadores 0/1/2 llegan cuando no son la fila seleccionada y la fila seleccionada se omite. El cuerpo mide 44/80 bytes y usa un salto ARM a `0x002892C0`; la IPS acumulativa modifica solo el slot y pasa roundtrip. Build ARMv6K 204/204 y revisión independiente aceptados; runtime no ejecutado. [Registro](../function-records/0x0029edfc.md), [contrato](../agent-work/h2-0029edfc-contract.md).

Actualización H2 (2026-11-02): `ui_func_002c615c` ya tiene C++ tipado con ABI `u64` (cociente en `r0`, resto en `r1`). Pasó 368 casos directos, dos composiciones reales con el helper original `0x002BF9F0`, control de destino erróneo y revisión independiente. El build ARMv6K completo pasó 204/204 TUs. El parche offline aislado preserva seis ramas que entran al cuerpo antiguo; no se fusionó en la imagen acumulada porque ambos usan la misma cueva. El updater `0x0029F278`, runtime y equivalencia integral siguen pendientes. [Registro](../function-records/0x002c615c.md), [integración](../agent-work/h2-2c615c-production-integration.md), [revisión](../agent-work/h2-2c615c-production-independent-review.md).

Actualización H2 (2026-11-02): el updater completo del cursor `camp_func_0029f278` está expresado como C++ tipado y clasificado `non_matching`. La integración vigente escribe en su slot original un cuerpo de 1.024 bytes más una tabla local de 4 bytes, conserva el sufijo original, pasa roundtrip IPS y no encontró entradas estáticas alineadas al interior. La base H2 acumulada pasa 158 diferenciales directos, cuatro composiciones con el `TitleConfig_Calc` original, cuatro con la imagen acumulada y el control de destino erróneo; también pasó revisión independiente del dominio H2, incluidos IDs especiales `(6,15)`/`(5,14)` y el eje 1 omitido. El helper de consulta original sigue siendo dependencia; no se capturan directamente los modos exteriores en esa revisión. Build 204/204. No se ejecutó runtime y no se asignan nombres físicos a IDs de input. [Registro](../function-records/0x0029f278.md), [integración](../agent-work/h2-29f278-slot-integration.md), [revisión H2](../agent-work/h2-29f278-h2setup-independent-review.md).

Actualización H2 (2026-11-02): `0x001FF3C4`, el mover de cursor llamado por ese updater, quedó como C++ tipado y ledger `non_matching`. Run006 pasó 162/162 casos directos, cuatro composiciones del `TitleConfig_Calc` y el control de destino erróneo; una revisión independiente fresca pasó 171/171, las mismas cuatro composiciones y confirmó los helpers locales dentro del slot de 880 bytes. El build ARMv6K pasó 204/204 TUs. Un IPS instalado en el slot original de la imagen H2 que ya contiene `0x0029F278` pasó roundtrip; una segunda revisión confirmó que solo cambia ese slot y volvió a pasar las cuatro composiciones acumuladas. Los casos cubren las dos condiciones corregidas a partir de ARM: C2/C1 sin gate de contador y ancho original para comparar, y B0/B2 con N de `SUBS` para overflow. Query/input/calibración siguen originales; no se ejecutó runtime. [Registro](../function-records/0x001ff3c4.md), [integración directa](../agent-work/h2-001ff3c4-integration.md), [integración acumulada](../agent-work/h2-001ff3c4-slot-integration.md), [revisión](../agent-work/h2-001ff3c4-independent-review.md), [contrato](../agent-work/h2-001ff3c4-contract.md).

Actualización H2 (2026-11-02): la dependencia de consultas `0x00254CA8` también está en C++ tipado y clasificada `non_matching`. Run005 pasó 76 casos directos dentro del dominio donde el axis reader escribe sus dos muestras, tres composiciones con el mover `0x001FF3C4` original, el control de destino erróneo y el build ARMv6K 204/204. La revisión independiente fresca pasó 89 casos comparables, las tres composiciones y el control; aprobó solo ese dominio acotado. El original puede leer valores previos de stack cuando `0x0027FBC8` no escribe; el candidato no declara equivalencia en ese caso y aún no se ha demostrado que H2 lo excluya. FPSCR caller-saved, NaN/Inf, mapeo físico y scheduling tampoco se afirman. [Registro](../function-records/0x00254ca8.md), [contrato](../agent-work/h2-00254ca8-contract.md), [integración](../agent-work/h2-00254ca8-integration.md), [revisión](../agent-work/h2-00254ca8-independent-review.md).

Actualización H2 (2026-11-02): `script_vm_func_00297674` se expresa ahora como getter C++ de palabra completa: lee el puntero de `0x0043E190` y devuelve la palabra en `+0x1C` sin normalización ni guarda nula. Pasó siete valores directos, la fault nula, tres controles de mutación y 28 composiciones con el `TitleConfig_Calc` original; se ejecutó también el `0x002BDAC0` original en la rama de valor cero. El cuerpo ocupa los 20 bytes del slot y difiere en dos bytes; la IPS de slot único pasa roundtrip. Revisión independiente aceptada y build ARMv6K completo 204/204. Runtime y ciclo de vida del objeto no probados. [Registro](../function-records/0x00297674.md), [contrato](../agent-work/h2-00297674-contract.md), [revisión](../agent-work/h2-00297674-independent-review-run001.md).

Actualización H2 (2026-11-02): `script_vm_func_002b8b78` se convirtió a C++ tipado como transición de perfil de seis slots; la etiqueta `Sound_PlaySE` no refleja por sí sola toda su conducta. Pasó revisión independiente, 23 diferenciales finales, dos slices de llamada ARM originales para `0x99` y el `0xDC` condicional, cuatro controles mutantes y compilación de nueve TUs afectadas. El cuerpo ocupa 332/340 bytes, la IPS modifica solo ese slot y las seis instrucciones de rama resuelven a cinco destinos ARM únicos y pares; el dato de prioridades se liga a la tabla ROM verificada `0x00402550`. Se mantienen originales sus cinco dependencias. El caller condicional es evidencia estática/slice, no reachability natural; no se ejecutó runtime ni se verificó salida de audio. [Ficha](../function-records/0x002b8b78.md), [evidencia](../agent-work/h2-sound-playse-production-conversion.md), [revisión](../agent-work/h2-sound-playse-independent-review-002b8b78.md).

Actualización H2 (2026-11-02): `camp_func_002aea28`, el selector de payload de perfil invocado dos veces por `0x002B8B78`, ahora tiene C++ tipado y ledger `non_matching`. Pasó revisión independiente, 16 casos directos de límites unsigned/null, dos slices originales de caller (`0x99`/`0xDC`), tres controles mutantes y compilación de los tres TUs afectados. La IPS de 56 bytes pasa replay; sus tres relocaciones ARM quedan en los helpers TBB originales. Las composiciones usan hooks para los resultados TBB y los otros servicios del wrapper, por lo que no validan el lifecycle de recursos ni reachability natural del callback. [Ficha](../function-records/0x002aea28.md), [evidencia](../agent-work/h2-profile-lookup-production-conversion.md), [revisión](../agent-work/h2-profile-lookup-independent-review-002aea28.md).

Actualización H2 (2026-11-02): `Tbb_GetRowCount` (`0x002C0E4C`) tiene ahora una definición C++ tipada; valida puntero, magic `TBL1` y stride no nulo, y conserva la división unsigned en el helper ARM original `0x002C6C10`. Pasó revisión independiente, 13 diferenciales directos, cinco composiciones con `0x002AEA28`, tres controles mutantes y compilación de los tres TUs afectados. El objeto compilado contiene una relocation de rama de cola; resuelta en su VMA final, la función coincide byte por byte y mantiene ledger `matching`, con IPS limitado al slot. Los datos TBB usados son sintéticos y no se comprobó runtime/audio. [Ficha](../function-records/0x002c0e4c.md), [evidencia](../agent-work/h2-tbb-row-count-production-conversion.md), [revisión](../agent-work/h2-tbb-row-count-independent-review-002c0e4c.md).

Actualización H2 (2026-11-02): `camp_func_002b8794`, el actualizador de seis registros de perfil llamado por `0x002B8B78`, ahora tiene C++ tipado y clasificación `non_matching`. Pasó revisión independiente, 12 casos directos de límites/registro y dos slices originales de caller (`0x99`/`0xDC`) con las seis llamadas reales por slice; se detectaron tres mutaciones y compilaron los dos TUs afectados. La función actualiza las tablas de registro y el estado por-slot del manager; el caller usa mode 0. Los fixtures manager son sintéticos, los otros servicios del wrapper son hooks y no se probó runtime/audio. [Ficha](../function-records/0x002b8794.md), [evidencia](../agent-work/h2-profile-slot-registry-production-conversion.md), [revisión](../agent-work/h2-profile-slot-registry-independent-review-002b8794.md).

Actualización H2 (2026-11-02): `ui_func_002b85bc`, el selector de transición de perfil invocado por `0x002B8B78`, se convirtió a C++ tipado y se registra como `non_matching`. Pasó revisión independiente, nueve casos directos, dos slices originales de caller (`0x99`/`0xDC`) y cinco controles mutantes. La auditoría corrigió la multiplicidad: el estado 8 hace tres llamadas al servicio, y un estado 7/9 mutado a 8 hace cuatro en total. El cuerpo de 372 bytes cabe en el slot de 472 bytes; sus once ramas resueltas son llamadas ARM pares y la IPS cambia solo ese slot. Los fixtures de perfil son sintéticos y los servicios controlados; no se validó reachability natural, lifecycle vivo, runtime ni audio. [Ficha](../function-records/0x002b85bc.md), [contrato](../agent-work/h2-profile-selector-contract-002b85bc.md), [evidencia](../agent-work/h2-profile-selector-production-conversion-002b85bc.md), [revisión](../agent-work/h2-profile-selector-independent-review-002b85bc.md).

Actualización H2 (2026-11-02): `camp_func_002aa268`, llamada dos veces por `0x002B85BC` en el modo distinto de 1, ahora tiene C++ tipado y clasificación `non_matching`. Pasó 12 casos directos, la composición con el selector ARM original y cuatro mutaciones; una revisión nueva también comprobó la rama de modo 1 hacia `0x002BDAC0`. El cuerpo ocupa 68/72 bytes sin relocaciones y la IPS modifica solo el slot. Las pruebas sintéticas cubren índices y selectores de 32 bits, solapamientos tabla/registro, faults parciales y las dos llamadas con `(record,0,1)`. No se ha demostrado lifecycle vivo, reachability natural, runtime ni audio. [Ficha](../function-records/0x002aa268.md), [contrato](../agent-work/h2-profile-record-copy-contract-002aa268.md), [evidencia](../agent-work/h2-profile-record-copy-production-conversion-002aa268.md), [revisión](../agent-work/h2-profile-record-copy-independent-review-002aa268.md).

Actualización H2 (2026-11-02): `ui_func_002a8a8c`, servicio global del contador signed usado por las rutas de estado del selector de perfil, se convirtió a C++ tipado y se marca `non_matching`. Pasó 11 casos directos, dos composiciones del selector tipado y cuatro mutaciones; una revisión independiente agregó rutas duplicadas, ruta de perfil nuevo y recarga con estado 9→8. El cuerpo ocupa 36/36 bytes sin relocaciones. El helper devuelve el puntero `P+0x600` mientras decrementa solo el halfword signed de `P+0x64C` cuando es positivo; este contador global no es el byte de estado que el selector vuelve a leer. Se alineó la declaración cross-TU y se compilaron las unidades afectadas. No se verificó runtime/audio ni validez natural del puntero global. [Ficha](../function-records/0x002a8a8c.md), [contrato](../agent-work/h2-status-service-contract-002a8a8c.md), [evidencia](../agent-work/h2-status-service-production-conversion-002a8a8c.md), [revisión](../agent-work/h2-status-service-independent-review-002a8a8c.md).

Actualización H2 (2026-11-02): `ui_func_002c17d4` se reconstruyó como consulta lógica tipada de un bit: valida IDs 0–30, aplica la compuerta/máscara de su fila y selecciona una de dos palabras globales por bit 0 del modo. Pasó 134 comparaciones directas, cuatro controles y 17 composiciones con el dispatcher original `0x002C1830` en modo 2. El cuerpo ocupa el slot de 92 bytes sin relocaciones; 80 bytes cambian y la IPS de un solo slot pasa roundtrip. Revisión independiente aceptada y build completo 204/204. El modo se carga como byte en C++ frente a la carga de palabra original, limitado a RAM ordinaria alineada. La actualización completa del cursor, la fuente de refresco disputada, runtime y mapeo físico no se establecen. [Registro](../function-records/0x002c17d4.md), [contrato](../agent-work/h2-002c17d4-contract.md), [revisión](../agent-work/h2-002c17d4-independent-review-run001.md).


Actualización H2 (2026-11-02): `camp_func_002892c0` se convirtió a C++ tipado para el clamp y ajuste de posición del cursor. Pasó 1.220 casos directos y 360 composiciones con el `0x0029EDFC` original; la integración final-address compila el símbolo de producción (136 bytes sin relocaciones), usa un `B` ARM par hacia `0x003FEE64`, recompone la IPS de cuatro registros sin solapamientos y detecta el control de destino desplazado. La base Calc-only pasó 68 casos. La cueva completa de la imagen acumulada Calc/Draw/Secondary está asignada, así que esta integración no se presenta como parte de esa imagen. Runtime y `0x0029F278` completo no se ejecutaron. [Registro](../function-records/0x002892c0.md), [informe](../agent-work/h2-002892c0-production-integration.md), [revisión de contrato](../agent-work/h2-002892c0-independent-review.md). La revisión independiente aceptó esta integración acotada y el build ARMv6K completo pasó 204/204 TUs en `build/h2-002892c0-full`.


Actualización de integración H2: el registro de regiones `0x002B88C4` y el resolver indexado `0x002BF6D0` ahora se componen juntos en la imagen run-013, con una IPS de dos slots. Los 242 bytes modificados quedan dentro de ambos spans; los tres `BL` usan entradas ARM pares. La comparación del caller original pasó 58/58 casos y la revisión independiente repitió 58/58 con otro seed. La evidencia usa fixtures controlados y excluye el residuo temporal bajo SP del divisor; scheduler, vida del manager, runtime y equivalencia integral siguen sin probarse. [Integración](../agent-work/h2-b88c4-bf6d0-cumulative-integration.md), [revisión](../agent-work/h2-b88c4-bf6d0-cumulative-independent-review.md).


Corrección del servicio lógico H2: el helper `0x002C6C10` es unsigned divmod y con divisor cero retorna `r0=0xFFFFFFFF`, `r1=dividendo`; no invoca un error. La matriz mode-0 anterior no cubría selector cero; un probe adicional pasó 7/7 casos del caller original y la ficha ahora registra esta extensión. Un C++ full-domain de forma directa ocupa 52 bytes frente al slot de 48 y genera una llamada no resuelta a `__aeabi_uidiv`; no se reemplaza el original hasta resolver el tamaño y la dependencia. [Ficha](../function-records/0x002c6c10.md), [reconstrucción](../agent-work/h2-002c6c10-divmod-contract-recon.md), [probe selector cero](../../build/agent-work/H2-semantic/h2-logical-mode0-zero-selector/run002/report.json).

Actualización H2 (2026-11-02): `ui_func_00296f18` se convirtió a C++ tipado y se marca `non_matching`. La comparación offline pasó 61 casos directos, un fault de límite reproducido, tres mutaciones detectadas y los cuatro destinos ARM `BL`; el cuerpo ocupa 68/72 bytes sin relocaciones. El caller original `0x0029FAE8` y la imagen con reemplazo de un slot ejecutaron exactamente las llamadas `(cursor,3,3)` y `(cursor+0x28,1,1)`, y coincidieron en los diez words de ambos ejes, write trace completo, registros preservados, SP y retorno. Ambos `start` finales valen 1; el 2 es solo el valor intermedio del helper. La revisión independiente no encontró counterexample en RAM ordinaria alineada. Runtime, lifecycle completo y equivalencia del título siguen sin probarse. [Ficha](../function-records/0x00296f18.md), [runner/evidencia](../agent-work/h2-296f18-cursor-axis-conversion.md), [revisión](../agent-work/h2-296f18-independent-review-run002.md).

Actualización H2 (2026-11-02): `camp_func_0029fae8` se convirtió a C++ tipado y se marca `non_matching`. El cuerpo compilado ocupa 392/452 bytes; el runner resuelve siete `BL` del ELF a entradas ARM originales alineadas. Las pruebas offline pasaron 60/60 casos tanto en coordinator como en revisión independiente, incluyendo gates signed, ambos valores `wrap_row`, ambos valores `repeat`, traza exacta y estado final de TitleConfig, y un control de destino incorrecto detectado. El wrapper conserva las dependencias originales para divmod y los escritores de ejes/IDs; su helper hoja final se expresa como store C++ y mantiene el retorno crudo `r0=cursor+0x28`. El contrato probado se limita a RAM ordinaria alineada y dimensiones positivas para la ruta activa. No cubre vida completa, scheduler/input, audio ni runtime del título. [Ficha](../function-records/0x0029fae8.md), [contrato](../agent-work/h2-0029fae8-contract.md), [runner/evidencia](../agent-work/h2-29fae8-independent-review.md).
