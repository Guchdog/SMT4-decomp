# Revisión independiente: sondeo de entradas distintas de APT Utility-4

## Resultado

El sondeo implementa el paso por encima del breakpoint con el orden esperado y las comprobaciones de hilo/PC/LR/SP son conservadoras. No encontré un defecto que impida una captura runtime breve después de que el coordinador verifique las puertas offline requeridas. La clasificación de LR evita atribuir causalidad a una coincidencia: usa `consistent_with_direct_bl`, `consistent_with_ee0_fallthrough` o `unresolved_possible_tail_or_indirect`, y declara que LR por sí solo no demuestra una ruta de salto de cola.

La limitación de cobertura concreta y no bloqueante es que el test de este sondeo inyecta una pérdida de respuesta al reinsertar `Z0` y verifica que el colector propague la excepción, pero no compone ese fallo intermedio con `capture_session/execute` para observar el callback fatal. La capa compartida tiene pruebas sintéticas de `capture_session`/`execute` para pérdidas de Z0, z0 y `s`, retry de terminación y conservación del socket/stage cuando el estado del proceso sigue desconocido. La relación de llamada es estática y directa (`base.collect_hits = collect_distinct_entries`), así que el gap no bloquea una captura aislada; conviene añadir la composición específica antes de promover evidencia.

## Protocolo RSP inspeccionado

1. `capture_session` instala `Z0` en `0x002C0EFC`. La captura de cada entrada requiere respuesta `T05` y un campo `thread` simple en hexadecimal. El colector selecciona ese hilo con `Hg`, lee registros y exige `r15 == 0x002C0EFC`.
2. Retira el breakpoint con `z0` y exige `OK`; luego selecciona el mismo hilo para continuar (`Hc`) y envía `s`. La respuesta al paso también debe ser `T05` del mismo hilo. Tras `Hg`, lee registros otra vez y exige `r15 == 0x002C0F00`, además de LR (`r14`) y SP (`r13`) idénticos. La fuente ARM fijada confirma que la instrucción de entrada es `0xE3A01000` (`MOV r1,#0`).
3. Si habrá otra observación, reinstala `Z0` y exige `OK` antes de devolver el hit y antes del próximo `continue`. En el hit final no lo reinstala. Los límites admiten entre 1 y 4 hits; el runtime debe usar un packet separado con límites de tiempo y de hits acotados.
4. Al terminar normalmente, `capture_session` hace `z0` final, `D` y cierre del socket. El stub de Azahar restaura la instrucción original en una retirada presente; si ya no existe, la rutina `RemoveBreakpoint` no-op y el handler igualmente responde `OK`. Por tanto, el `z0` final tras el hit final es idempotente.
5. Una respuesta ambigua durante la colección se propaga a `capture_session`; con el callback `on_fatal` de `execute`, termina el proceso aislado antes del detach/cierre. Si la terminación no queda confirmada, las pruebas compartidas muestran que no envía `D`, no cierra el socket y conserva el staging. Un timeout de `continue` sin error devuelve hits parciales; un timeout/error en la secuencia de paso o reinserción va por la ruta fatal.

`Z0`/`z0` son breakpoints software: el stub inserta el trap en el código guest y restaura la instrucción al retirarlo. La salida declara correctamente ausencia de paquetes explícitos RSP `M/P/X` y cero entradas lógicas; no significa que el target nunca tenga una escritura de memoria transitoria.

## Ruta y clasificación estática

El verificador del `code.bin` fijado comprueba el hash, alineación ARM, palabra de entrada y lista exacta de ramas alineadas directas: BL desde `0x002C0F6C`, `0x002C1260` y `0x002C1304`; B desde `0x00106F00`, `0x0010700C`, `0x002A8164` y `0x002C5638`. La rutina excluye expresamente rutas indirectas y Thumb. Estas listas respaldan el inventario estático, no demuestran cuál camino produjo un hit runtime.

Las pruebas simulan las respuestas RSP y registros: verifican la secuencia exacta de dos hits, que la reinserción ocurre antes del siguiente continue, la omisión de reinserción tras el hit final, timeout parcial, PC/hilo incorrectos y fallo de reinserción. No ejecutan instrucciones del guest. Los tests compartidos cubren limpieza fatal y orden de terminación/cierre con datos sintéticos, no con Azahar real.

Límites adicionales: `stop_thread` acepta solo `T05` con un identificador simple, no formatos de hilo `pPID.TID`; comprueba señal SIGTRAP pero no exige un subcampo `swbreak` específico. El PC, el hilo y el paso comprobado reducen ambigüedad, pero la captura no prueba por sí sola que todo `T05` proceda del breakpoint software esperado. La prueba de timeout comprueba que la reinserción aparece, mientras que la prueba de dos hits comprueba el orden exacto de paquetes.

## Validación realizada

- 26/26 hashes declarados por el packet coinciden; el inventario incluye runner, tests, fuentes fijadas, documentación y el `code.bin` original. No incluye saves ni perfiles.
- `python -B -m unittest tests.test_h2_apt_utility4_distinct_entry_probe tests.test_h2_apt_utility4_tailstep_probe tests.test_h2_apt_utility4_interior_probe tests.test_h2_apt_utility4_caller_probe tests.test_h2_rsp_fatal_execute_integration -v`: 62 tests pasaron, exit 0.
- `verify_interior_entry` sobre el `code.bin` fijado pasó con la entrada y las siete ramas listadas arriba.
- No ejecuté Azahar, GDB, tests contra un guest, ni compilaciones. No accedí a saves o perfiles reales ni a copias desechables. Los tests crean solo marcadores sintéticos temporales.

## Identidades

- Runner: `tools/h2_apt_utility4_distinct_entry_probe.py` — SHA-256 `dbb2c150f9ad300685c2194f01ebff55029fc777cfa2e8cac7058ac3902311f5`.
- Tests del sondeo: `tests/test_h2_apt_utility4_distinct_entry_probe.py` — SHA-256 `f09b3c11f06aeef8d55484849623747168389e27a36c36dc57d08bcc1f9f51eb`.
- Imagen original fijada `code.bin` — SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Packet de revisión: 26 inputs coincidentes; detalle en `checks/input-hash-audit.json`.

## Siguiente acción

El coordinador puede preparar una única captura runtime con un packet runtime fresco y sus puertas offline aprobadas, límite pequeño de hits (por ejemplo, 2) y deadline corto del runner. Mantener las etiquetas LR como compatibilidad, no como prueba del caller. Antes de promover la evidencia, añadir un test sintético que fuerce fallo de reinserción desde el colector distinct a través de `capture_session/execute`, verificando terminación antes de desconectar y sin `D`.
