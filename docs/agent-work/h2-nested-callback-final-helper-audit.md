# Auditoría estática de `0x00286928` (helper final del callback H2)

**Alcance.** Lectura estática del ARM original fijado y de los informes/pins del run-002. No ejecuté pruebas, builds, emulador, debugger ni acceso a perfil/guardado; no edité fuente, ledger ni board.

## Identidades verificadas

- Los 16 hashes `input_sha256` del packet de esta auditoría coinciden.
- Packet dinámico run-002: `task.json` SHA-256 `293bcdb2c658ecab44e05f4de0e167fcd687ed4f0a414ddc0d1c0f68c5b8ca8a`; captura `autonomous-gdb-verification.json` SHA-256 `9381f48e52c533f0a2508817deb516cefa59228732fe2a1fd14fe9fc3afddbfe`; handoff SHA-256 `662c8e64522ab796733cfa6019526f3e9c5bde9354b3a4f3f640841ddd3f015d`. Los tres coinciden con los hashes fijados en el packet de esta auditoría.
- Imagen original `extracted/exefs/code.bin`: SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, 3.633.152 bytes. `0x00286928` tiene span de 820 bytes (fila de ledger `matching`); los 410 halfwords ARM embebidos en `src/engine/leaf_batch45_a.cpp` reproducen exactamente esos 820 bytes. Hash del cuerpo: `13599a73fefa7f8ed72d8251e769b2302486c973169be524785830699b7f7c6c`. Hash del TU: `7839733a03da5cd79e4553c33cc4206f85fb942613354e25f92c7d0108eddcda`.

## Qué captura realmente run-002

La captura pareada reporta 20 eventos anidados en cada lado, 19/19 checkpoints coincidentes y los eventos normalizados iguales. En los 40 eventos el target leído de la tabla y el target observado en `BLX` son `0x00221168`; el retorno raw del callback es `r0=0`, y el handler externo ID 8 retorna `r0=2` después del nested ID 33. Este es el alcance preciso del reporte; no dice que se capturó directamente el helper `0x00286928`.

El callback estático `0x00221168` llama a `0x00286928` como su última llamada y restaura stack/registros sin sobrescribir `r0`; por ello, condicionado a ese código fijado, el retorno raw 0 observado en el callback implica que el helper final produjo 0. El observador no tiene breakpoint en `0x00286928` y los eventos no contienen sus seis argumentos, el PC de salida del helper ni los campos/punteros que decidieron la rama. La atribución de la dirección y el retorno es sólida al nivel callback; la causa interna del cero no está capturada.

Run-002 también informa `passed=true` para el recorrido guionizado, pero `h2_full_acceptance_supported=false`, `physical_input_mapping_proven=false`, `input_scheduling_proven=false`, `controlled_lifecycle_completed=false` y `same_session_reentry_both=false`. El input usó una consulta lógica determinista de un fotograma. La traza es contexto dinámico acotado, no cierre de H2 ni prueba de entrada física.

## Seis argumentos documentados por el caller

La secuencia de `0x00221168` llama al helper con lo siguiente. Los tres primeros son resultados/cadenas de helpers previos y no tienen un tipo o significado establecido por esta evidencia.

| Entrada a `0x00286928` | Fuente estática del caller | Uso estático observado en el helper |
|---|---|---|
| `r0` | Resultado de `0x0028686C`, guardado en `r7` | Conservado como arg1 y reenviado como `r1` a `0x0028E974`. |
| `r1` | Resultado de `0x00296F60`, guardado en `r6` del caller | Arg2 se recupera del área guardada en stack y se reenvía como `r2` a `0x0028E974`. |
| `r2` | Resultado de la segunda llamada a `0x00289640` | Se copia a `ip` y solo se compara con cero para elegir una ruta. No se dereferencia directamente en este cuerpo. |
| `r3` | Constante `6` | Se conserva en `r6`; selecciona la rama por defecto `r5 = [0x0043E188+4]`, deja en cero los flags iniciales usados en `+0x5E/+0x5F`, y selecciona el literal raw `0x035AB9FF` para guardar en `r5+0x10`. |
| `[sp]` | Constante `1` (arg5) | Se carga en `r4`; su valor distinto de cero habilita llamadas a `0x002C4BF0` y `0x002B90F0`, usando `[r5+4]` con flags `0x20` y `0x40`. También se guarda en `r5+0x36`. |
| `[sp+4]` | Constante `0` (arg6) | Se carga en `s16` y, en una de las llamadas a `0x0028E974`, se copia como palabra a un slot de stack. Esto prueba el movimiento por un registro VFP single, pero no asigna por sí solo un tipo semántico al argumento. |

El frame del helper guarda `r0-r3`; tras `push`, `vpush {d8}` y `sub sp,#0xc`, carga args 5/6 desde offsets `sp+0x48` y `sp+0x4c`. En la llamada principal a `0x0028E974`, prepara `r0=r5`, `r1=arg1`, `r2=arg2`, `r3=arg4`, más stack `0x1A`, `1` y el valor de `s16`. La ruta secundaria a ese helper usa stack `0x1A`, `1`, `0`.

## Ruta del cuerpo y retornos

`0x00286928` es ARM, 202 instrucciones antes del literal pool de 12 bytes al final del span. El literal `0x0043E188` en `0x00286C50` da la base usada por el selector; los otros dos literales son `0x035AB9FF` y `0x320202FF`. Para `r3=6`, se usa la rama por defecto con el valor literal `0x035AB9FF`.

El helper selecciona `r5` desde la tabla de `0x0043E188`: arg4/`r6==12` elige `base+0x0C`; 11, 13, 14, 15 o 19 eligen `base+8` (algunos valores normalizan `r6` o setean flags); otros valores, incluido el 6 del caller, eligen el puntero cargado desde `base+4`. Los dos primeros stores a `r5+0x2D` y `r5+0x5E` ocurren antes de la primera comprobación de nulidad. Más adelante también hay un store incondicional a `r5+0x10`. En el caso real del caller, el puntero `[0x0043E188+4]` debe ser válido para que esas instrucciones se ejecuten; el cuerpo no lo valida primero.

Las lecturas explícitas relativas a `r5` incluyen `+0x04`, `+0x08`, `+0x09`, `+0x18`, `+0x2E` y `+0x35`. Las escrituras locales incluyen `+0x2D`, `+0x5E`, condicionalmente `+0x5F`, `+0x36`, `+0x10`, condicionalmente `+0x2E`, algunos estados en `+0x08/+0x20/+0x35`, y las áreas indexadas `+0xA12`, `+0xA13+i`, `+0xA1A+2*i` para seis iteraciones, con una escritura condicional a `+0xA26`. No asigno nombres a estos campos. Las llamadas directas pueden tener efectos adicionales no caracterizados aquí.

Los callees directos de la función son `0x002C1F28`, `0x002B89A0`, `0x002B8D24`, `0x0028E974`, `0x002B787C`, `0x0028DF98`, `0x002C4BF0`, `0x002B90F0`, `0x002F5B2C`, `0x002D65B4`, `0x0028DF70`, `0x002B8CCC`, `0x002B8B78`, condicionalmente `0x002B8584`, `0x0028DF54`, `0x0028DF3C` y `0x0028DF0C`. No encontré una llamada indirecta dentro de este cuerpo.

Todos los caminos normales llegan a uno de dos valores explícitos antes del epílogo común:

- `0x00286BE4` escribe `r0=0`; las rutas que llegan aquí incluyen fallos de las consultas `0x002C1F28/0x002B89A0`, rutas de actualización de estado, y el retorno después de `0x0028E974` y de los seis elementos indexados. El helper no clasifica esos casos como error en este código.
- `0x00286C38` escribe `r0=1`; se alcanza desde más de una rama de estado/consulta. `0x00286C40` hace una llamada adicional a `0x0028DF54`, escribe `r0=1` y salta al epílogo. Ambos conservan ese valor a través de `0x00286BF4`.

Así, un retorno 0 es una salida explícita y ordinaria del helper, pero el código por sí solo no revela el significado de alto nivel de 0/1. El run-002 muestra 0, y el flujo estático del caller deja pasar ese valor. No determina cuál de las condiciones/callees produjo la ruta cero en los eventos observados.

## Desconocido y siguiente evidencia mínima

Siguen desconocidos los valores runtime de `r0-r2`, el valor de arg3 (solo se sabe que el helper lo prueba como cero/no cero), los punteros en la tabla `0x0043E188`, los bytes de estado seleccionados en `r5`, los retornos de los callees y qué rama llevó a `0x00286BE4`. El reporte run-002 no captura ninguno de esos datos dentro del helper. Tampoco autoriza etiquetar los campos ni interpretar semánticamente el cero.

La evidencia mínima que discrimina la rama causal es una captura RSP futura, acotada y de solo lectura, en el helper ya identificado: en entrada registrar hilo/PC, `r0-r3`, `[sp]`, `[sp+4]`, `0x0043E188` y el puntero/bytes necesarios de `r5`; registrar el PC en `0x00286BE4` frente a los retornos 1 en `0x00286C38/0x00286C40`, junto con `r0` al salir y el ID/evento callback que lo contiene. Esto explica la rama sin inventar nombres. Cualquier afirmación de significado o C++ tipado requiere además contratos de las estructuras y callees.

## Método y límites

Se verificaron los hashes de entrada declarados, el hash de la imagen y el span de fuente; se inspeccionó el ARM con Capstone 5 desde el `code.bin` fijado y se cotejó el cuerpo codificado en `.hword`. No se ejecutaron pruebas, builds, emulador ni debugger. No se leyó el guardado ni perfiles. Esta revisión resuelve el retorno estático que compone a la traza; no cierra H2.