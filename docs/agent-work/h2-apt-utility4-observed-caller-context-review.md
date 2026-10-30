# Revisión independiente: contexto completo del caller APT Utility-4

## Resultado

Reproduje el contexto offline fijado sobre ambas bases. El caller original en `0x00103E4C`, el bridge original en `0x002C5624`, la entrada candidata en `0x002C0EFC` y la continuación del caller se ejecutan dentro de Unicorn. El runner informa 40/40 casos por base, cero divergencias, y mi repetición obtuvo el mismo resultado. Recomiendo aceptar este resultado como evidencia contextual offline limitada.

El alcance no equivale a una ejecución completa del juego: el wrapper APT y las otras funciones externas listadas se sustituyen por hooks; el JSON no conserva muestras de los bytes `.data` tocados por caso; `.bss`, efectos de servicio, callers Thumb/indirectos y runtime siguen sin cubrirse. No hice cambios a candidato, runner, tests, imágenes base, saves, perfiles, ledger ni board; no usé Azahar/GDB.

## Proveniencia y reproducción

Los 19 hashes declarados en `run-001/task.json` coincidieron. El original mide `0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; la base H2 compuesta mide lo mismo, SHA `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`. La fuente candidata conserva SHA `1f7228e30cfdb3c14497f96fdce3bc65845ad65bb4b3b5491c5ab2b382742e06`; mi objeto recompilado tiene SHA `f9dd6fa8373017a61a5d777bd6220387f9150d11f2f0e4aae78d72bb2dc4be56`.

Corrí, secuencialmente y con un solo compilador, el runner `tools/h2_apt_utility4_inplace_context_composition.py` con las rutas exactas del original y de la base compuesta. Exit 0; 40 casos por base; cero fallos; candidato de 40 bytes. Los hashes de las imágenes parcheadas que produjo son `6f4196b5edac295adb56442e7b2c3fb6d40fc1f5793be6e8882fe590f7e10baf` y `788530a1b1ad7d4f361228cbd0e4b87885b37606a8f3485c52e5390ae3223179`, respectivamente. También ejecuté el test focalizado: exit 0, 1 test pasó. Ese test unitario solo verifica la función Python `caller_result` para cuatro pares de readiness; la ejecución de código ARM viene del runner.

## Caller, bridge y observación de LR

La desensamblación ARM del original muestra este camino:

- El caller empieza en `0x00103E4C`, guarda `r4-r6/LR` y prepara recursos mediante llamadas externas. En `0x00103E74` carga `r5` desde el literal en `0x00103EEC`; el valor es `0x00465198`.
- En `0x00103E78` hace `mov r0,#1` y en `0x00103E7C` `strb r0,[r5]`. Luego el `BL` real en `0x00103E80` llega a `0x002C5624`; su LR es `0x00103E84`.
- El bridge ejecuta instrucciones del `code.bin`; no está en la lista de hooks. En `0x002C5624` hace `cmp r0,#0`; `0x002C5628` carga `r0` desde el literal en `0x002C5640`, cuyo valor es `0x0044E3B0`; `0x002C562C` pone `r1=1`; `0x002C5630` hace `strb r1,[r0]`; `0x002C5634` tiene `beq 0x002C563C`; y el `B` real en `0x002C5638` salta a `0x002C0EFC`.
- Desde este caller concreto el `BEQ` del bridge no se toma: su `r0` de entrada acaba de ser establecido a 1. Al candidato llega el puntero `r0=0x0044E3B0` y el LR sigue en `0x00103E84`, porque el bridge usa `B`, no `BL`.
- Después del retorno de la entrada, el caller continúa en `0x00103E84`, reemplaza `r0` por 1 y hace `strb r0,[r5,#1]` en `0x00103E88`. Ejecuta sus llamadas siguientes y termina en `0x00103EDC` (`pop {r4,r5,r6,pc}`), con destino de retorno `0x01000000` del harness.

La comparación captura por hook la entrada a `0x002C0EFC` y exige exactamente una fila con `LR=0x00103E84` y `r0=0x0044E3B0`, tanto en original como en candidato. El campo `observed_lr_at_candidate` del JSON está escrito desde una constante, pero el aserto de `compare()` valida ese LR contra el valor capturado durante cada ejecución Unicorn. Esto confirma la observación offline y es coherente con el LR runtime previo resumido en el contrato; esta tarea no repitió ni revalidó la captura GDB original.

La entrada del candidato recibe el valor de retorno del wrapper, pero el caller lo sobrescribe inmediatamente con `mov r0,#1` en `0x00103E84`. Por tanto, los cinco valores devueltos por el stub del wrapper varían la llamada, pero no controlan el resultado posterior del caller. La propagación cruda de `r0` se cubre en el test aislado de la entrada, no en esta ventana contextual.

## Hooks, branches y límites de ejecución

`execute()` arranca en `0x00103E4C`, fija LR inicial a `0x01000000` y corre hasta allí tras la instrucción de retorno del caller. No hay hook para `0x002C5624` ni `0x002C5638`; esas instrucciones y los stores caller/bridge se ejecutan desde la imagen fijada. La comprobación también exige no observar una entrada al bridge como hook.

Sí se interceptan `0x002C541C`, `0x002C3B00`, `0x002C4244`, `0x00110030`, `0x0011001C`, `0x00110744`, `0x002C57B4`, `0x002C57A4` y el wrapper `0x002B5A1C`. Para llamadas no readiness el hook entrega `r0` controlado (pseudoaleatorio en el caso) y retorna poniendo `PC=LR`; en `0x002C57B4/0x002C57A4` entrega los dos resultados readiness solicitados. El wrapper captura sus seis palabras, estado ARM y alineación de SP, devuelve el valor seleccionado y vuelve a LR. Esos cuerpos reales, incluidos posibles stores, callbacks o efectos globales, no se ejecutan.

Los escenarios readiness `(1,0)`, `(0,1)`, `(0,0)` y `(0xffffffff,0)` cubren los dos resultados de las comparaciones/branches del caller en `0x00103EC0..0x00103ED4`; solo `(0,0)` devuelve 1. No varían el `r0=1` que alimenta el bridge, así que el `BEQ` bridge a `0x002C563C` no se prueba. El runner usa dos seeds (`41`, `2026`) y cinco retornos del wrapper (`0`, `1`, `0x7fffffff`, `0x80000000`, `0xffffffff`), total `2 × 4 × 5 = 40` casos por base.

## Memoria global

Los offsets usados por el runner (`file_offset=0x0032B000`, VMA `0x0042B000`, tamaño `0x0004B644`) coinciden con `config/game_info.json`. La comparación calcula hash y runs de cambio para todo ese segmento `.data` inicializado después de cada ejecución y exige igualdad original/candidato. Ambos globals están dentro de ese rango, pero son distintos:

| Uso | Literal/carga | VMA | Offset `.data` | Offset en `code.bin` | Bytes iniciales en ambas bases |
| --- | --- | ---: | ---: | ---: | --- |
| `r5` del caller | literal `0x00103EEC` | `0x00465198` | `0x3A198` | `0x00365198` | `01 01 00 00` |
| byte del bridge | literal `0x002C5640` | `0x0044E3B0` | `0x233B0` | `0x0034E3B0` | `00 00 00 00` |

El caller escribe 1 en los primeros dos bytes de su work area (ya valen `01 01` en la imagen). El bridge escribe 1 en el primer byte de su global separado, que inicia en cero. La ejecución compara el `.data` completo, incluidos ambos rangos, entre original y candidato. Sin embargo, `report.json` solo conserva `cases_by_base`, fallos y escenarios readiness: no guarda por caso `data_changed`, los hashes de `.data`, las filas de trace ni los bytes después. La repetición independiente confirma el resultado agregado, pero tampoco deja esas muestras persistidas; no afirmo haber observado un delta guardado byte a byte.

La región `.bss` comienza en `0x00477000`, justo al final del mapeo del `code.bin`, y no se mapea ni compara. Los efectos de los hooks tampoco se reflejan en `.data`. Así que la frase correcta es “compara el segmento `.data` inicializado completo en este escenario con dependencias stubbed”, no “compara toda la memoria global del proceso”.

## Recomendación

Aceptar el reporte como evidencia contextual offline: demuestra la ruta caller→bridge→entrada→continuación con el código original y el candidato, prueba los branches readiness modelados y detecta divergencias dentro de `.data` inicializado en las dependencias simuladas. Mantener explícitos los límites: sin cuerpos reales de APT/servicios y otras llamadas, sin delta `.data` por caso persistido, sin `.bss`, sin puente-zero alternativo, sin callers Thumb/indirectos y sin runtime Azahar. H2 y cualquier promoción permanecen abiertos.
