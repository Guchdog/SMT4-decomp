# Revisión independiente: candidato APT Utility-4 in-place (`0x002C0EFC`)

## Resultado

No encontré un defecto en la afirmación offline acotada: el código C++ compila a 40 bytes, mantiene el contrato de seis palabras y una llamada ARM al wrapper `0x002B5A1C`, cabe en la entrada original de 44 bytes, y pasa las ventanas de callers que el harness declara. Recomiendo aceptar este resultado como validación offline de la entrada bajo wrapper controlado. No recomiendo promoción de producción ni equivalencia H2: el wrapper real, los efectos IPC/servicio, el contexto completo y la continuación de callers, Thumb/entradas indirectas y runtime siguen sin cubrirse.

No modifiqué el candidato, runners, tests, base original, imagen compuesta, ledger ni board. No lancé Azahar/GDB ni accedí a saves o perfiles.

## Proveniencia e identidades

Verifiqué los 30 hashes `input_sha256` del packet `run-001/task.json`: 30/30 coincidieron. El original y la imagen H2 compuesta vuelven a tener estas identidades exactas:

| Base | SHA-256 |
| --- | --- |
| `reference/code.bin` original | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| `code.h2-final.bin` compuesto | `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446` |

Ambos tienen el tamaño fijado por el runner (`0x377000` bytes). El candidato C++ tiene SHA `1f7228e30cfdb3c14497f96fdce3bc65845ad65bb4b3b5491c5ab2b382742e06`; el objeto compilado de ambas reproducciones tiene SHA `f9dd6fa8373017a61a5d777bd6220387f9150d11f2f0e4aae78d72bb2dc4be56`; el cuerpo ya resuelto tiene SHA `cfd2bc4d713a0ffca01cfaac9112339f1c8f4b85a0ddbd0053ad4dc408bce2d5`.

## Fuente, cuerpo ARM y ABI

La fuente declara `Word` como `unsigned int`, un wrapper `extern "C"` con seis argumentos de 32 bits, y una función `extern "C" __attribute__((minsize))` que llama `apt_wrapper(4, 0, 0, 0, 0, 0)` y devuelve el `Word` sin alterarlo. La compilación registrada usa Clang ARMv6K (`--target=armv6k-none-eabihf`, `-mcpu=mpcore`, `-mfloat-abi=hard`, `-O2`). El símbolo `candidate_002c0efc` mide 40 bytes.

La desensamblación del símbolo del objeto fue:

```text
00  push {r9, r10, r11, lr}
04  mov r0, #0
08  str r0, [sp]
0c  str r0, [sp, #4]
10  mov r0, #4
14  mov r1, #0
18  mov r2, #0
1c  mov r3, #0
20  bl  <R_ARM_CALL apt_wrapper>
24  pop {r2, r3, r11, pc}
```

El `push` reserva 16 bytes, igual que el original (`push lr` más 12 bytes); al wrapper le llegan `r0-r3=(4,0,0,0)` y `[sp], [sp+4]=(0,0)`. Si el SP de entrada está alineado a ocho, permanece alineado al llamar. El epílogo restaura SP y `r11` y devuelve el `r0` del wrapper; `r2/r3` son caller-saved. El harness observa las seis palabras, estado ARM y alineación de SP, y compara `r4-r11`, retorno y SP restaurado.

La única relocation del **símbolo candidato** es `R_ARM_CALL` (tipo 28) en offset `0x20`/dirección `0x002C0F1C`, símbolo `apt_wrapper`, addend implícito `-8`. El linker offline la resuelve al word ARM `0xEBFFD2BE` (bytes little-endian `be d2 ff eb`); decodificando `P+8+sign_extend(imm24)*4` el destino es exactamente `0x002B5A1C`, y el BL está dentro del rango/alineación ARM. Precisión: el objeto contiene además una función de control `wrong_command` con su propia `R_ARM_CALL`, y relocations `R_ARM_PREL31` en `.ARM.exidx`; la afirmación de una sola llamada aplica al símbolo aplicado, no a todo el objeto.

El cuerpo ocupa `[0x002C0EFC,0x002C0F24)`. Los cuatro bytes finales originales `[0x002C0F24,0x002C0F28)` permanecen iguales y el siguiente cuerpo comienza en `0x002C0F28`; el rango protegido `[0x002C0F28,0x002C1320)` mide 1016 bytes y se mantiene idéntico entre original y compuesto, además de mantenerse intacto al aplicar el candidato offline. La protección también compara la entrada precedente/fallthrough, wrapper y dos helpers contra el original al usar la base compuesta. No se usa la antigua cave de `0x003FEE54`.

## Caller sites y reproducción diferencial

Decodifiqué los siete branches en ambas bases; sus words no cambian y todos apuntan a `0x002C0EFC`:

| Dirección | Tipo | Word ARM | Destino |
| --- | --- | --- | --- |
| `0x002C0F6C` | BL | `0xEBFFFFE2` | `0x002C0EFC` |
| `0x002C1260` | BL | `0xEBFFFF25` | `0x002C0EFC` |
| `0x002C1304` | BL | `0xEBFFFEFC` | `0x002C0EFC` |
| `0x00106F00` | B | `0xEA06E7FD` | `0x002C0EFC` |
| `0x0010700C` | B | `0xEA06E7BA` | `0x002C0EFC` |
| `0x002A8164` | B | `0xEA006364` | `0x002C0EFC` |
| `0x002C5638` | B | `0xEAFFEE2F` | `0x002C0EFC` |

Reproduje secuencialmente el runner `h2_apt_utility4_inplace_caller_composition.py`, un compilador por ejecución, con salida separada para cada base. Cada base tuvo 10 casos en cada una de las siete instrucciones de branch y la entrada fallthrough `0x002C0EE0`, más 16 llamadas directas a la entrada: 96 casos por base. Usa dos seeds (`19`, `2026`), cinco retornos (`0`, `1`, `0x7fffffff`, `0x80000000`, `0xffffffff`), caller instructions originales y wrapper controlado. Ambas reproducciones finalizaron con `passed=true`, cero divergencias y los mismos hashes de objeto/cuerpo. Los tres negativos pasaron: el cambio de command se detecta por la traza del wrapper; un cuerpo mayor de 44 bytes se rechaza; y un destino de llamada incorrecto no pasa la verificación del branch.

| Base | Imagen candidata offline SHA-256 | Casos caller + fallthrough | Casos entrada directa |
| --- | --- | ---: | ---: |
| Original | `6f4196b5edac295adb56442e7b2c3fb6d40fc1f5793be6e8882fe590f7e10baf` | 80/80 | 16/16 |
| H2 compuesto | `788530a1b1ad7d4f361228cbd0e4b87885b37606a8f3485c52e5390ae3223179` | 80/80 | 16/16 |

También ejecuté `python -B -m pytest -p no:cacheprovider -q tests/test_h2_apt_utility4_inplace_experiment.py`: exit 0, 3 tests pasaron. Cubren la resolución del BL y el body de 40 bytes, rechazo de destino/relocation incorrectos y composición que conserva bytes fuera del body y rechaza exceso de tamaño.

## Límites

- El hook sustituye `0x002B5A1C`; no ejecuta su flujo real, SVC/IPC, buffers, callback de error ni efectos globales. El wrapper y los helpers de `0x002C0EE0` son stubs controlados.
- Las ventanas empiezan en los branch sites reales, pero no ejecutan el setup anterior ni la continuación después del retorno. Para los `B` el harness usa un LR de parada sintético. El fallthrough ejecuta el tramo desde `0x002C0EE0`, con hooks para sus dos helpers.
- El runner usa Unicorn en `UC_MODE_ARM`; no valida callers Thumb, BLX/entradas indirectas ni el mapa/permisos X de Azahar. El reporte de ambos cuerpos es evidencia offline de imagen, no runtime.
- Los casos comparan las observaciones que enumera el harness; no certifican todo el estado guest ni servicios. Los negativos son de command, tamaño y resolución del destino, no controles de IPC/error.
- La entrada cubre el retorno de un helper APT, no todo H2 (`titleConfig`, sonido, persistencia/reinicio o escenario de juego integrado). No cambia el ledger ni autoriza una clasificación de equivalencia.

## Recomendación

Aceptar este candidato para su contrato aislado y ubicación in-place bajo las comprobaciones offline registradas. Mantenerlo experimental. Antes de producción, hace falta el escenario integrado que ejercite el wrapper/servicio real y caller setup/continuaciones relevantes, además de cualquier entrada Thumb/indirecta demostrada por evidencia. Runtime sigue `not_run`.
