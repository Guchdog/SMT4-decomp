# Revisión independiente: probe interior APT Utility-4

**Packet:** `h2-apt-utility4-interior-probe-review`, run-001  
**Revisor:** `h3_read_return_review`  
**Alcance:** solo inspección estática y pruebas offline; no inicié Azahar/GDB ni accedí a saves o perfiles.

## Conclusión

El wrapper prepara un probe acotado y puede pasar a consideración de un packet runtime independiente, con la condición explícita de que `Z0` sí modifica transitoriamente código guest. No es una observación de solo lectura. El runner de una sola invocación intenta retirar el breakpoint, desconectar y terminar su propio proceso de Azahar; no declara runtime observado ni prueba semántica H2. No encontré un error que requiera cambiar el runner antes de preparar ese packet.

Dos límites deben quedar visibles. `configure_runner()` modifica globals del módulo runner base y no los restaura, por lo que el wrapper es apropiado como CLI aislada de una invocación, no como API reusable o idempotente dentro de otro proceso. Además, si se pierde la respuesta de `Z0` después de que el stub lo haya aplicado, `capture_session()` no puede saber que debe enviar `z0`; en la ruta completa `execute()` el proceso hijo propio se termina en `finally`, que es la contención final de ese caso. Una captura fuera de esa ruta no tendría la misma garantía.

## Identidad y revisión estática

Los 19 SHA-256 declarados en el task packet se recomputaron y coinciden. También coincide el SHA del `code.bin` con la imagen fijada por el packet de implementación: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

El runner escanea ramas A32 alineadas y fija tres `BL` directos a `0x002C0EFC` (`0x002C0F6C`, `0x002C1260`, `0x002C1304`) y cuatro `B` (`0x00106F00`, `0x0010700C`, `0x002A8164`, `0x002C5638`). Los tres enlaces implican LR `0x002C0F70`, `0x002C1264`, y `0x002C1308`. El escaneo comprueba esos inventarios contra el binario fijado antes de continuar. Como declara el audit, esto cubre branches directos alineados ARM; no enumera llamadas indirectas ni rutas Thumb.

La clasificación de LR separa coincidencias con los tres `BL` de valores no resueltos que podrían venir de los cuatro `B` u otras rutas. Las dos LR de llamadas directas a `0x002C0EE0` se etiquetan `consistent_with_ee0_fallthrough`, no como una atribución probada a un salto de cola. El campo conserva el límite de que LR por sí solo no establece el origen de un `B`.

## Wrapper, packet y gates

`configure_runner()` cambia `BREAKPOINT`, lista de callers, clasificador, IDs de tarea permitidos y `static_contract` en el objeto importado `base`; su wrapper conserva la función original y añade `verify_interior_entry()`. `main()` configura y llama inmediatamente `base.main()`. Esto evita editar el runner compartido y funciona en el proceso CLI de una invocación. El cambio global persiste si el módulo se usa como librería; llamarlo otra vez puede envolver de nuevo `static_contract`. El test de configuración usa `patch.multiple`, así que limpia los globals del test, pero no prueba una reutilización repetida sin ese parche.

El runner base verifica los hashes de todas las entradas declaradas y rechaza caminos relativos con traversal o resolución fuera del checkout. Restringe task ID y output root al directorio H2 que corresponde a ese ID; la ruta runtime requiere attestation fresca dentro de su packet y valida cuatro gates con estado `passed`, hash del reporte y campos ARM/Thumb requeridos. El task de implementación no puede llegar a staging/runtime: la ejecución exige manifiesto de dependencias y falla antes de crear el stage si no existe. Los controles y pruebas relevantes están cubiertos por el test focalizado combinado.

El probe usa exactamente un breakpoint `Z0` en `0x002C0EFC`, cap de cuatro hits, deadline monotónico compartido para operaciones RSP y una gracia única acotada de cleanup. Tras attach, intenta `z0`, luego detach y cierre de socket; la ruta envolvente termina su proceso hijo propio, comprueba listener y conserva solo el log diagnóstico permitido. Errores de limpieza hacen fallar el resultado. No envía paquetes RSP explícitos `M`, `P` o `X`, ni inyecta entradas lógicas.

La afirmación sobre escritura guest queda confirmada por el `gdbstub.cpp` fijado (SHA-256 `bb345fcaca1e09f41a5d5f6941a4eef5d98e0b0257b15aa98ce993c0a22025d6`): `AddBreakpoint` mapea tanto Z0 como Z1 a `Execute`; `CommitBreakpoint` escribe la instrucción `btrap` mediante `Memory().WriteBlock` (líneas 1722–1731), y `RemoveBreakpoint` restaura las instrucciones guardadas con otro `WriteBlock` (líneas 553–567). El efecto temporal es, por tanto, una modificación real de memoria/código guest, aunque el protocolo no mande M/P/X.

Caso límite de cleanup: `breakpoint_set` se marca solo después de recibir `OK` a `Z0`. Si el paquete se aplica pero se pierde su ACK/respuesta, la limpieza local no intenta `z0` porque no conoce que se insertó. En el flujo `execute()`, el `finally` termina el proceso hijo que posee ese guest y solo elimina el stage tras verificar que el proceso terminó. Un packet runtime debe conservar esta ruta íntegra y fallar ante errores de cleanup; no debe llamar `capture_session()` suelto y luego mantener vivo al guest.

## Validación ejecutada

Ejecuté únicamente:

```text
python -m unittest tests.test_h2_apt_utility4_interior_probe tests.test_h2_apt_utility4_caller_probe -v
```

Resultado: exit 0, **45 tests OK**. El log está en `build/agent-work/H2-semantic/h2-apt-utility4-interior-probe-review/run-001/checks/focused-tests.txt`, SHA-256 `5840fedc7818574b19bbe7a20686e9d4184f204c0b4c25cb7a82e87538033432`.

Hashes revisados: wrapper `tools/h2_apt_utility4_interior_probe.py` = `5354839a773ab34a5ff4159315efe9f5986a1386308d3ab2fd7cd7b48fcebd39`; pruebas especializadas = `12ba68d8b564a8fd4f29e4a6057e52a9d196831678ab7d1989e0d3a80da5e9bf`; runner base = `10043a4062f11e24329fd4c2ff3b693230707784d1a21b8a458595f11e0e6a14`; pruebas base = `7e95296b8fd40248ca30c31490173881cfa2f955231fb5f918f37ffa3e2719e9`.

## Evidencia y siguiente paso

- `compiled`: `not_run`; no se compila código en esta tarea.
- `arm_differential`: `not_run`; el escaneo estático no es differential de ejecución.
- `caller`: `not_run`; inventario de callsites fijados, sin caller runtime observado.
- `runtime`: `not_run`; no hubo emulator/GDB.

Recomendación: el integrador puede preparar un packet runtime nuevo, congelar y rehashear wrapper, base, helper y gates, y repetir gates offline antes de cualquier launch. El objetivo de runtime debe ser capturar LR/regs en el `BL`/`B` site ya definido; aceptar explícitamente el parche temporal Z0. Mantener el proceso hijo aislado y asegurar que limpieza completa/terminación del proceso ocurra incluso con respuesta Z0 ambigua. No inferir callers indirectos/Thumb ni equivalencia funcional de una captura.
