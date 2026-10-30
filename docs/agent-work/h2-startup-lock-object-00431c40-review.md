# Revisión independiente: auditoría estática del objeto H2 `0x00431C40`

## Dictamen

**Acepto la auditoría estática dentro de sus límites.** Recalculé los xrefs directos de literal y desensamblé de forma independiente las rutas A32 relevantes en el `code.bin` fijado. La carga literal única, la publicación del puntero, la espera sobre `base+0x64`, la posible señalización sobre `base` y la ruta de limpieza concuerdan con el informe y con las fuentes Azahar fijadas. La comparación de rutas Run-017/Run-028 usa el resumen autorizado de `docs/milestones/H2-audio-settings.md`; no abrí el directorio crudo de Run-028.

La conclusión se sostiene en la forma acotada: **no repetir otro inicio genérico ni volver a sondear el mismo wrapper SVC sin una pregunta nueva**. Run-016 ya resume los argumentos del sitio genérico de espera, y Run-028 solo agrega un recorrido previo distinto sin link demostrado al dispatcher H2. El informe identifica el dato de Run-028 que falta (`r1`) y no lo infiere a partir de la lectura de memoria. La auditoría no demuestra que Run-028 se haya quedado bloqueado, que ambos valores sean el mismo objeto por causalidad, ni que el lock explique la divergencia.

## Identidad y hashes

El task packet review run-002 tiene SHA-256 `c3f916799ab2a3e2c65849c869769c950dbbc5982c67ba78c011b6c4026e7fe2`. El `code.bin` fijado tiene SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; la base de carga declarada es `0x00100000`. Volví a comprobar los 15 hashes de entrada del paquete review run-002 y todos coincidieron. También recalculé los hashes de entradas del `static-audit-evidence.json`, incluidos el informe y task de Run-017 (validación por digest; no necesitaba leer el JSON runtime), y todos coincidieron. El informe estático revisado conserva SHA-256 `7763c42a424df49541c416bbed5d58306a5c80d4c2f2f66eec5ee468937ba171`; su índice de evidencia, `bb6b3c4157431db677ca44aeaea71216dae0f7239bfd45603f4c5a265534f349`; y su handoff, `52b5e94b29f7df89e0bc31767ba51c62beb17366c9cbf97c024f663e34af3ed0`.

Fuentes Azahar fijadas y verificadas: `address_arbiter.h` `44b5974ffc30fa15d586e21367d5ec2ffd98148b682dc7c40b3c33265e698b39`, `address_arbiter.cpp` `5882bd6b6cc686c56a862860b14c06bbcfbdbc6dbdb85ce03757232f0fd3ac8d` y `svc.cpp` `d55eeaefa017906c2cc189c42986c8aaf5aae92a7a04e6bd3bda68255dfe85b8`. El resumen de hito fijado tiene SHA-256 `c3a972af68ab31728a796ded35830e192f547ddc196f79ad15148a33b8284aa7`.

## Xref y rutas confirmadas

La búsqueda independiente de la palabra little-endian `40 1c 43 00` devuelve un único offset de archivo `0x29A20`, que corresponde a VA `0x00129A20`. El escaneo A32 de `LDR` PC-relativos da un único xref: `0x001299A0`, instrucción `E59F0078`; con PC=VA+8, el destino es `0x00129A20`. El escaneo de `LDR literal` Thumb-1 no produjo candidatos. Esto confirma el literal/xref directo solicitado, no todo flujo indirecto ni referencias formadas por MOVW/MOVT.

La lectura de los bloques A32 confirma los enlaces relevantes:

- `0x0012992C` carga el literal `0x00471A70` en `r4`. En `0x001299A0`, el código carga el literal `0x00431C40` y limpia campos del objeto; `0x001299F8` guarda ese puntero en `[r4+0x1C]`, es decir, en `0x00471A8C`. `0x00431C40` es un valor de pool usado como dirección, no datos que residan en el pool.
- `0x00129A28` carga el literal `0x00471A70`; `0x00129A2C` carga el puntero publicado `[+0x1C]` y `0x00129A30` salta a `0x0013AD64`.
- En `0x0013AD64`, el objeto se conserva en `r4`, se invoca el helper de adquisición `0x002C3AA8`, y en la rama relevante `0x0013AD88` lo libera mediante `0x002C3A24` antes de pasar `r0=base+0x64` a `0x002C3628`.
- `0x002C3628` lee `[r4]`; en la rama que espera por el valor `-2`, prepara `r1=r4`, `r2=1`, `r3=0` y argumentos de timeout cero antes de llamar `0x002A8898`. El wrapper ejecuta `SVC #0x22` en `0x002A88A4`. La dirección de esa ruta estática es `base+0x64`.
- `0x002C3A24` decrementa `[base+8]`; al llegar a cero limpia `[base+4]` y salta a `0x00138FC0` con `r0=base`. Ese helper actualiza atómicamente `[base]` y, cuando su condición de contador indica que hay esperadores, llama al mismo wrapper con `r1=base`, `r2=0`, `r3=1`, timeout cero. Es una ruta de `Signal` sobre `base`, distinta del `WaitIfLessThan` sobre `base+0x64`.
- `0x0011D06C` carga `[0x00471A70+0x1C]` y llama a `0x00129B1C`. La rutina de limpieza cierra los handles/campos que toca, limpia miembros y libera el lock base mediante `0x002C3A24`; luego escribe `0xFFFFFFFF` en `base+8`.

La fuente fijada define `ArbitrationType::Signal=0` y `WaitIfLessThan=1` (`address_arbiter.h:25-30`). La tabla de SVC mapea `0x22` a `SVC::ArbitrateAddress` (`svc.cpp:2275`; implementación desde línea 1131). En `address_arbiter.cpp:123-163`, `Signal` reanuda el número solicitado (o todos para valor negativo) y `WaitIfLessThan` compara como `s32` el dword de la dirección con el umbral antes de poner el hilo en espera. Esto describe la implementación HLE fijada; no define semántica de hardware o significado del objeto para el juego.

## Diferencia de rutas y conclusión sobre otra sonda

Según el resumen fijado de hito, Run-017 registra 18 queries lógicas, 12 entradas y 12 retornos de handler, llega a State 2 y repite ID 8 en `0x001A07CC`. Run-028, en cambio, tiene `logical_queries=[]`, cero llamadas de navegación y ningún handler/array de State 2; registra un caller previo (`0x0010316C`, `0x0010319C`, `0x001031A4`) y termina antes de `TitleMain_Init` en `PC/LR=0x002A88A8/0x001465A8`. El resumen cita una lectura de diagnóstico `0xFFFFFFFE/0x1FF82800/1` en `0x00431C40`, pero no reporta `r1` en la llamada de Run-028. No equiparo esa lectura con el argumento de dirección de su SVC ni concluyo que la palabra sea la causa del timeout.

Run-016, en el mismo resumen, ya registra en el callsite `0x001465A4` `r0=1, r1=0x00431C40, r2=1, r3=0` y una rama de reintento. El listing confirma que `0x001465A4` llama al wrapper `0x002A8898` y que `0x001465A8` es el retorno siguiente; por tanto, otro stop genérico en ese wrapper solo volvería a describir un sitio ya acotado. El resumen de Run-028 no demuestra el `r1` de esa corrida ni relaciona su caller nativo con el ID 8 de Run-017. La afirmación correcta es que **no se justifica otra sonda genérica con la evidencia actual**. Si una futura revisión precisa la pregunta distinta de cómo ese caller se conecta (o no) con el dispatcher, tendría que justificar y pinnear una observación caller-específica; la auditoría actual no autoriza ni necesita otro lanzamiento.

## Límites y ejecución

No asigné nombres funcionales a los miembros ni interpreté el objeto como lock de hardware. El escaneo literal no resuelve todas las referencias indirectas. La comparación Run-028 se limita al resumen de milestone; no se abrieron sus archivos runtime ni su carpeta, y no se accedió a guardados/perfiles. No corrí builds, tests, Azahar ni debugger. No afirmo causa de la divergencia, deadlock, finalización de State 2 o equivalencia H2.

Comprobaciones realizadas: búsqueda y xref ARM/Thumb por Python de solo lectura; desensamblado Capstone A32 de los rangos listados en `static-audit.md`; inspección de las tres fuentes Azahar fijadas y del resumen de milestone; recomputación de hashes del paquete y evidencia. Todas terminaron con exit 0.

