# Revisión independiente: candidato APT Utility-4 `0x002C0EFC`

## Recomendación

El candidato pasa como implementación aislada de la secuencia ARM que llama al wrapper fijo con seis palabras y devuelve su `r0` sin alterarlo, bajo el wrapper controlado del harness. Reproduje dos semillas de 64 casos cada una y los tres negativos detectan los defectos previstos.

No es un reemplazo directo de la función original en su ubicación actual: el símbolo compilado ocupa 56 bytes frente a los 44 bytes originales. El runner escribe los 56 bytes en `0x002C0EFC`, por lo que su caso diferencial pisa 12 bytes del inicio de la función siguiente (`0x002C0F28..0x002C0F33`). Esos bytes pertenecen a instrucciones originales (`0xE92D4FFF`, `0xE24DD044`, `0xE3A04000`); el harness no ejecuta la vecina y, por eso, no detecta ese daño de integración. Mantenerlo como candidato aislado experimental. Antes de integrar hay que acordar una ubicación/trampolín o una secuencia que quepa, y probar que los bytes vecinos y callers permanecen válidos.

## Contrato, argumentos y ABI

Los 11 words ARM fijados en `0x002C0EFC..0x002C0F24` son:

`E3A01000, E52DE004, E24DD00C, E3A00004, E1A03001, E1A02001, E58D1000, E58D1004, EBFFD2BE, E28DD00C, E49DF004`.

Confirman `r1=0`, `push lr`, reserva de 12 bytes, `r0=4`, `r2=r3=0`, dos ceros en `[sp]` y `[sp+4]`, llamada directa y retorno/restauración. En el `BL`, la envoltura recibe `(4,0,0,0,0,0)`: cuatro primeras palabras en `r0-r3` y las palabras quinta/sexta en stack. La entrada original mide 44 bytes y exige la alineación AAPCS que aporta el caller.

La firma candidata `Word (*)(Word,Word,Word,Word,Word,Word)` y su `return original_wrapper(...)` conservan los seis words y el patrón de retorno de 32 bits. La compilación del replay produjo ARMv6K `elf32-littlearm`; el disassembly usa `push {r11,lr}`, reserva 8 bytes adicionales, almacena dos argumentos en stack, carga el literal absoluto `0x002B5A1C` y ejecuta `BLX r12`. Con SP de entrada alineado a 8, el SP en el wrapper queda alineado a 8 y el epílogo restaura SP, r11 y PC. El hook observa estado ARM (`thumb=false`); esto no constituye una prueba de callers Thumb.

## Objeto y relocations

Los dos replays compilados tienen el mismo SHA-256 de objeto (`15d1a89d…141cb34`). Los tamaños de símbolo son 56 bytes para `candidate_002c0efc` y `wrong_command`, y 60 para `wrong_argument` y `discarded_return`. El extractor usado por el runner confirma cero relocations asociadas a los cuatro símbolos de código. Una lectura independiente con `llvm-readobj` muestra además cuatro relocations `R_ARM_PREL31` en `.rel.ARM.exidx`; por tanto es preciso decir “código de las funciones sin relocations”, no “objeto entero sin relocations”. El literal de wrapper es absoluto y depende de que `0x002B5A1C` permanezca válido en el entorno de integración.

## Harness, cobertura y negativos

Los dos reportes originales (SHA `18353af9…ab0572` y `6cc3bb49…284c16`) están fijados en el packet. Ambos registran `passed=true`, 64 casos, cero fallos, mismo hash del `code.bin` y del candidato, y los tres negativos esperados. Los replays independientes (semillas 1 y 2) reprodujeron esos resultados y el mismo hash de objeto.

Por retorno se usan los cinco patrones `0`, `1`, `0x7FFFFFFF`, `0x80000000`, `0xFFFFFFFF` más 59 words aleatorios. El wrapper sintético captura los cuatro registros de argumento y los dos words de stack, SP modulo 8 y estado Thumb; luego devuelve el `r0` elegido y regresa mediante LR. El comparator revisa PC/SP, `r0`, `r4-r11`, memoria de datos y la región de stack activa que compara el harness. `wrong_command`, quinto argumento distinto de cero y retorno descartado fallan en las aserciones esperadas.

Límites y posibles falsos positivos:

- El hook reemplaza el cuerpo real de `0x002B5A1C`: no ejecuta IPC/SVC, buffers, efectos globales, callback de error `0x002C14F4`, adquisición/liberación ni servicios. El valor alto `0x80000000` solo prueba propagación del retorno del stub.
- No hay caller composition de los BL/B directos, fallthrough `0x002C0EE0`, entrada desde Thumb ni runtime. `UC_MODE_ARM` y `thumb=false` prueban solo el camino ARM del harness.
- Se compara memoria de datos y una región de stack declarada por el test, no toda la memoria guest. El stack scratch por debajo del SP inicial puede diferir; eso no demuestra equivalencia del wrapper/servicio.
- El replay superpone 56 bytes sobre una función de 44 bytes y no ejecuta la vecina. Así puede pasar para la función aislada mientras una instalación in-place corrompería código adyacente.
- Los controles solo cubren command, quinto argumento y retorno. No prueban callback de error ni efectos de servicio; no deben presentarse como controles de esas rutas.

## Evidencia ejecutada

- 20/20 hashes de entradas declaradas en el packet coincidieron.
- Reejecuté secuencialmente con un único slot: `python -B tools/h2_apt_utility4_entry_experiment.py --code build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/reference/code.bin --output build/agent-work/H2-semantic/h2-apt-utility4-entry-candidate-review/run-001/checks/replay-seed-1 --seed 1` y lo mismo con `replay-seed-2 --seed 2`. Ambos: exit 0, 64 casos, cero fallos y tres negativos detectados.
- `python -B -m unittest tests.test_h2_apt_utility4_entry_experiment -v`: 1 test pasó. Es una prueba del comparator; la cobertura de llamadas la aportan los replays Unicorn.
- `llvm-objdump -d --no-show-raw-insn` confirmó el flujo ARM y el literal. `llvm-readobj --relocations --symbols` confirmó los tamaños y cuatro relocations `.ARM.exidx`.
- La revisión de las 20 entradas del packet y los hashes de los artefactos generados está en `checks/input-hash-audit.json` y `checks/object-audit.json`; disassembly, tabla de relocations y log de test están en `checks/`.

No ejecuté Azahar/GDB, runtime ni build canónico. No accedí a saves o perfiles. No modifiqué candidato, runner, tests, ledger ni board.
