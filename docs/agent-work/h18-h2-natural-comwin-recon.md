# H2: ruta de consulta lógica y cierre ComWin

## Hallazgo principal

`0x002C1830(0,1)` es la consulta lógica modo 1 para ID 0. No es una entrada de ComWin. El wrapper deriva a `0x002BFFBC(0)`, que devuelve 1 solo si `*(u32*)0x004650A8 & 1` está limpio y `*(u32*)0x004E3C58 == 1`; el valor se compara por igualdad exacta. El ID 0 tiene fila `0x004099C0` con gate 0 y máscara `1`. El refresher `0x001078D8` llama al lector `0x0011C5EC` para escribir el snapshot en `0x004E3C28`, marca disponibilidad en `0x004650A4`, y en una lectura disponible suma el contador ID0 si `state_word & 1` está activo o lo limpia si no. Una segunda actualización con el bit aún activo lo lleva a 2 y la query vuelve a 0. Es una inferencia acotada de un pulso lógico de un refresh; no identifica por sí sola ningún botón físico.

La cadena estática del refresher es `0x00101B8C` dentro del loop principal CRT → wrapper `0x0010B578` → refresher `0x001078D8` → reader `0x0011C5EC` → ring helper `0x0012A758`. El reader deriva el snapshot de un objeto/ring de input interno. El audit existente no ha establecido el significado de la bit 0, quién produce el ring desde el frontend, la cadencia de refresh frente a Calc, ni un seam seguro de input físico. No hay base para llamar al bit 0 «A» más allá de la etiqueta del escenario lógico.

## ComWin: entrada interior y límite de funciones

`ComWin_Init` (`0x0010A748`) registra el callback `0x0011B094` bajo el literal de nombre “ComWin Calc”. Ese callback es una entrada interior de 148 bytes (`0x0011B094..0x0011B128`) incluida en el span de ledger de `InfoWin_DrawUp` (`0x0011AE10`, 792 bytes); la cola está escrita como words ARM en `src/ui/window.cpp`. No tiene fila independiente en `config/functions.csv`. El mismo archivo contiene un placeholder C++ `ComWin_Calc(void*) { (void)arg; }`; no representa el comportamiento original en la dirección registrada.

La descompilación ARM de esa entrada interior carga el global `g_ComWinWork` (`0x0043E0F8`), despacha por el byte/word `work+8` y consulta widgets con `0x002BF9F0` en `work+0x3C` o `work+0xC8`. En estados 1 y 4, el resultado del widget mueve el estado (`1→2`, o `4→0`); estado 2 consulta el otro widget; la ruta común incrementa `work+0x0C` y retorna 0. La entrada no llama a `0x002C1830`, `0x002BFFBC` ni a los helpers de input. Por tanto no se debe describir esa task como el caller directo de la query lógica. Además, un candidato independiente para `0x0011B094` necesita resolver la superposición: su cuerpo coincide con bytes interiores del span `InfoWin_DrawUp`; no debe agregarse una fila/IPS solapada sin ajustar límites y composición.

## Caller conocido y caller no probado

El registro de función y el barrido de BL ARM en spans conocidos sitúan seis consultas H2 a `0x002C1830` dentro de `TitleConfig_Calc` (`0x001EA928`): `(9,1)`, `(4,0)`, `(3,0)`, las alternativas `(4|3,0)`, `(0,1)` y `(1,1)`. La llamada ID0/mode1 en `0x001EAE64` pertenece a la lógica de entrada de Calc; es evidencia de la query de H2 durante Calc, no evidencia de qué caller activa el stub en el tramo de readiness después de confirmar.

También se escanearon los spans con anotación fuente `.thumb` (136 spans): no apareció BL Thumb directo a `0x002C1830`. No se hallaron palabras absolutas alineadas a `0x002C1830`/`0x002C1831` ni palabras PREL31-like alineadas que resuelvan al dispatcher. Esto limita ciertos patrones estáticos, pero no excluye llamadas por BLX a través de task/function-pointer tables, código Thumb no representado en esos spans, bytecode/recursos externos o targets calculados. No afirmo ausencia global de callers dinámicos.

## Qué hace y qué no registra el runtime H2 más reciente

En `tools/h2_full_lifecycle_runtime_verify.py`, `wait_for_title_reset_after_confirm_with_comwin` calcula una condición a partir de `work_state==2` y los estados de los objetos guardados en `0x0043E18C/0x0043E190`, y temporalmente escribe un stub de 20 bytes directamente en `0x002C1830`. El stub devuelve 1 para `(r0,r1)==(0,1)` y 0 para el resto; se restaura cuando la condición ya no aplica. Esto sustituye el dispatcher completo: no ejecuta el lookup de `0x002BFFBC`, no observa el counter ni prueba al productor. Es un resultado lógico forzado, aunque la condición se active al observar estados que el runner atribuye al wait de ComWin.

El runtime JSON guarda `query_a_active` por frame, estados del work/objetos, retorno/PC de ReadyGate y 51 acciones scriptadas. No registra LR/SP/R0/R1 ni dirección de retorno de llamadas que caigan en el stub. El `return_pc` de esas observaciones es el retorno de `TitleConfig_IsReady`, no el caller de `0x002C1830`. Por eso el reporte no atribuye el hook a un callsite de readiness ni demuestra que `ComWin_Calc` invoque la query. La documentación del runner que llama al wait “ComWin_Calc waits for logical A” excede la evidencia directa del body de `0x0011B094`; requiere un trace/caller identificado antes de tratarse como contrato.

## Composición offline concreta

Existe ya evidencia separada reutilizable, pero no la composición completa que reemplaza el hook:

1. `tools/h2_1078d8_11c5ec_chain.py` compuso las dos rutinas de refresco/lectura, con un seam controlado de ring `0x0012A758`. Su informe/revisión registra 144/144 casos; los fixtures son sintéticos y no establecen fuente física/cadencia.
2. `tools/h2_logical_query_caller_composition.py` ejecuta el wrapper original `0x002C1830` y Calc real, pero presemilla los counters por escenario; no ejecuta el productor `0x001078D8` para generarlos.
3. `tools/h2_2c1830_experiment.py` prueba el wrapper con helpers/hooks deterministas; no es una entrada real.

Siguiente harness offline sugerido: partir de la máquina original y de la imagen acumulada H2 pinneadas; alimentar al seam de ring un snapshot válido con bit 0 apagado, luego encendido para exactamente una refresh de `0x001078D8`, invocar el dispatcher original/candidato como `(0,1)` y exigir counter `0→1`, retorno 1; repetir refresh con bit retenido y exigir `1→2`, retorno 0; soltarlo con refresh válida y exigir contador 0 y retorno 0; otro pulso debe volver a 1. Añadir casos de refresh no disponible, flag `0x004650A8 & 1`, control de bit vecino y negativos con contador !=1. Componer después el caller state-2/script callback cuyo LR sea observado o estáticamente identificado, y el evento de tarea pertinente; comparar las escrituras del panel, estado H2/readiness, ABI y trazas. Separadamente probar `0x0011B094` (estado 0..5, variantes de retorno de `0x002BF9F0`, writes a `+8/+0xC`, retorno/SP/registros) respetando que es entrada interior solapada.

Este harness probaría coherencia del protocolo lógico, no el mapeo físico. La tarea de runtime posterior necesita captura RSP/observer con el dispatcher original: al entrar en `0x002C1830` registrar R0/R1, LR/SP, guest thread y ticks de refresh; correlacionar la query `(0,1)` con el caller real y el estado de ComWin, sin modificar 0x2C1830. Sin un ring/evento real ya autorizado y un seam de sincronización, no es posible especificar un estímulo físico autónomo a partir de la evidencia estática actual.

## Proveniencia y límites

Imagen fijada: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Runner de ciclo H2: SHA-256 `676ee26cc8bc9a3d6da8bfe31885d13bce41aef4aa2bf206b050ecc538041545`. Audit del producer lógico: `docs/agent-work/h2-logical-input-table-producer-audit.md`, SHA-256 `152bb204dba87cfc448e2b5faac771ff6aca69448cacdda377ecfb9e87502543`. Composición/refrescador+reader offline: `docs/agent-work/h2-001078d8-0011c5ec-composition.md`, SHA-256 `3ba19790937d3bf89e648edcbabb6186a21be552f011a7cac01a2362d5dfb320`; revisión independiente SHA-256 `fbaac605992b34144a95a3c42670cef160e8ab092d44dfe5156a7b4ae0b33a39`. Runner actual no leído más allá de su contrato y código fuente; no se ejecutó build, test, emulador ni debugger.

El resultado acota el contrato lógico y corrige la atribución del callback ComWin, pero no identifica el caller dinámico del stub durante readiness, la correspondencia de bit 0 con un control, ni el mecanismo real que hace completar las tareas ComWin/script en el guest. El próximo candidato independiente recomendado es reconstruir y probar `0x0011B094` como sub-entry ARM real, con una auditoría de límites que preserve el span compuesto `InfoWin_DrawUp`.
