# Revisión independiente: `0x002BF6D0` — manager-slot lookup

## Dictamen

La implementación C++ y la evidencia offline respaldan una aceptación semántica acotada para una cadena legible de manager y para el espacio de índices `u32` de 32 bits. No encontré un contraejemplo en la aritmética de resto, el direccionamiento de la base ni la llamada a `0x002B0188`. Mantener la etiqueta de ledger `non_matching`: los bytes no son idénticos.

La composición de caller y el runtime no se probaron. El caller reconstruido en `asd_runtime.cpp` usa el grupo `0x1D` y el índice `0x572`, pero el diferencial reemplaza `0x002B0188` por un stub común y no ejecuta dicho caller. Esto no acredita el contrato real de ese servicio, la secuencia natural del scheduler ni la aceptación H2 completa.

## Identidad congelada y verificación

Los 13 inputs enumerados en `run001/task.json` existen y sus SHA-256 coinciden. El SHA de la imagen original es `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Extraje de forma independiente los 64 bytes originales desde `0x002BF6D0`; su SHA-256 es `9e094eadcb5aab79c862678e88525072bf7591c218962fdf72e21f0dc84ef071`.

El reporte congelado `build/agent-work/H2-semantic/h2-bf6d0-manager-slot-convert/run001/report.json` tiene SHA-256 `fd635c6ae6c632fea0146f9bf62c27204d8682f294610ac2d573b8d1376f45e3`. El SHA-256 del TU fuente reportado es `e43d6957e60b4ebd69931663eb530013fb40b4ed8132163c9730d086f73cea37`. Su cuerpo candidato mide 64 bytes y tiene SHA-256 `da0e26f67b50d912ef71ea93fff5b93110bc00a2dacf6e3c8ae4c73fa9b046e8`, igual al cuerpo hex reportado. No ejecuté compilador, runner, build ni emulador.

## Lectura del ARM original y aritmética

La descompilación de la imagen fijada muestra el flujo siguiente:

1. `push {r4, lr}`; guarda `r1` (índice crudo) en `r4` y llama a `0x002B0188` con el grupo original en `r0`.
2. Lee el literal `0x10624DD3`, usa `SMULL` y un desplazamiento aritmético para obtener el cociente signed entre 1000 truncado hacia cero. `SUB` resta la corrección de signo del cociente.
3. Calcula `q * -125`, luego `index + (q * -125 << 3)`, equivalente en 32 bits a `index - q*1000`; esto es el resto firmado. Multiplica ese resto por 5 y después por 4, para aplicar el stride de 20.
4. Lee `manager[+4]`, después el primer `u32` de esa dirección indirecta, y retorna `base + remainder*20` en `r0`.
5. `pop {r4, pc}` retorna y restaura el registro preservado.

El cuerpo termina con el literal usado por el `LDR` (en `entry+0x3C`); el retorno está en `entry+0x38`. Para todo `s32`, el cociente truncado al dividir por el divisor positivo 1000 produce un resto entre -999 y 999. `INT_MIN` no provoca el caso indefinido de división `INT_MIN / -1`; el cociente y `q*1000` caben en `s32`. El candidato interpreta los bits `u32` como `s32`, calcula `% 1000` y multiplica el resto por 20. El producto intermedio también está acotado y no desborda `s32`. La suma de base se hace como `u32`, reproduciendo el wrap de dirección de 32 bits del ARM.

Los dereferenciamientos presuponen manager, puntero indirecto y base legibles. No hay validación de null ni de punteros inválidos; esas entradas pueden fallar y quedan fuera del dominio soportado.

## Relocation, ABI y comparación de memoria

El reporte identifica una sola relocación `R_ARM_CALL` (tipo 28) en offset `0x18`, destino `0x002B0188`. Recalculé la codificación con la regla ARM `delta = target - (place + 8)`: en `0x00800000` el `BL` es `0xEBEAC05A`; en el slot final `0x002BF6D0` se vuelve `0xEBFFC2A6`, y ambos decodifican al destino esperado. El reporte lista esa misma relocation final.

El ARM original guarda/restaura `r4`; el candidato compilado guarda/restaura `r4`, `r5`, `r11` y `lr`. Ambos conservan `r4-r11` y `SP` y retornan por la dirección de continuación. El original ocupa 8 bytes de stack y el candidato 16; sus pushes son las únicas escrituras propias que se observan en los cuerpos inspeccionados. El comparador filtra las escrituras en `[SP-16, SP)`, por lo que no demuestra igualdad de bytes scratch del stack. Esa exclusión es explícita y razonable para este cambio de tamaño: la comparación conserva los registros restaurados, SP, retorno, argumentos del helper y escrituras fuera del scratch. No se debe convertir esto en una afirmación de igualdad de toda la memoria, incluyendo bytes de spill.

## Cobertura y límites del reporte

El reporte declara 2,001 valores dirigidos que enumeran cada resto firmado `-1000..1000`, 12 índices boundary dirigidos y 1,024 índices `u32` pseudoaleatorios con seed `20261105`; la unión tiene 3,031 índices distintos. Se prueban seis grupos representativos y se comprueba que cada llamada stub a `0x002B0188` recibe el grupo suministrado. No es el producto cartesiano de todos los grupos con todos los índices, ni un dominio exhaustivo de grupos.

Los dos controles compilados detectan el divisor mutado a 999 (`index=1000`: original `base+0`, mutante `base+20`) y el acceso mutado de `manager+4` a `manager+8` (base incorrecta en el fixture). El helper se compara en dirección temporal y en `0x002BF6D0` luego de reubicar el `BL`; se cotejan resultado, argumento del stub, registros callee-saved, SP, escrituras externas, terminación y faults. El reporte acredita 204/204 TUs ARMv6K compiladas; es un resultado reportado, no una compilación repetida por esta revisión.

`caller_composition` y `runtime` están explícitamente `not_run`. El caller real visible es `camp_func_002bf6d0(0x1D, 0x572)` dentro del state machine de camp slots; su composición no se ejercitó. Las pruebas fijan el resultado de `0x002B0188` a un manager sintético, así que no establecen su comportamiento real, accesibilidad de memoria en juego, lifetime, secuencia natural ni frecuencia de llamada.

## Recomendación

Aceptar solo la reconstrucción del helper bajo las precondiciones documentadas de punteros legibles y aritmética de direcciones de 32 bits; conservar `non_matching`. El reporte y las mutaciones son evidencia offline sólida del helper aislado. Cualquier afirmación mayor necesita composición con el caller real/servicio y, si se busca aceptación del escenario H2, validación runtime específica.
