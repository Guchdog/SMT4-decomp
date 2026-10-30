# Auditoría independiente: entrada interior APT Utility-4

**Tarea:** h2-apt-utility4-interior-entry-audit, run-002  
**Revisor:** h3_read_return_review  
**Conclusión:** 0x002C0EFC es una entrada ARM distinta de 0x002C0EE0 y contiene una preparación literal de command 4 antes de llamar al wrapper APT. Run-007 instrumentó 0x002C0EE0, no 0x002C0EFC. El orden del log coloca dos registros HLE command-4 después de insertar ese breakpoint y continuar, pero no atribuye las llamadas a un PID/caller. Además, el GDB stub fijado implementa tanto `Z0` como `Z1` con parches de instrucciones en memoria guest; no hay breakpoint de hardware sin escritura por esa ruta.

## Evidencia fijada

Los 11 hashes declarados por el packet run-002 se recomputaron y coinciden. El input adicional `build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src/core/gdbstub/gdbstub.cpp` tiene SHA-256 `bb345fcaca1e09f41a5d5f6941a4eef5d98e0b0257b15aa98ce993c0a22025d6`.

`code.bin`: SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, base virtual `0x00100000`. El log run-007: SHA-256 `38bc14fab4313c4a712a07d95cd6b830862412703ba988b34a6d908114a6d9d2`. Capture JSON: SHA-256 `0831a75e6d133f20b12306729229bceb8e6da8d7f5f3770660738fdd2e55cdf4`.

## Entradas y ramas directas A32

Capstone confirma ARM/A32 en 0x002C0EE0..0x002C0F24. La secuencia en 0x002C0EE0 pone `r0=0`, llama a 0x002BB7A0, pone `r0=1`, llama a 0x002BB774 y restaura `r4,lr`; 0x002C0EF8 es `mov r0,r0` (NOP). La entrada separada 0x002C0EFC empieza con `mov r1,#0`, guarda LR, reserva 12 bytes, pone `r0=4`, deja `r2/r3=0`, escribe cero en los dos slots de stack, llama a 0x002B5A1C y retorna con `pop {pc}` en 0x002C0F24. Esto describe registros e instrucciones literales, no la semántica de consola del wrapper/SVC.

Barrí palabras ARM alineadas en el `code.bin` fijado y calculé blancos B/BL con `PC+8+sign_extend(imm24)<<2`; desensamblé los blancos para descartar coincidencias de datos. Los únicos blancos directos del intervalo son 0x002C0EE0 y 0x002C0EFC:

| Callsite | Instrucción / palabra | Blanco | Efecto de enlace |
|---|---|---|---|
| 0x00102184 | `BL` / `EB06FB55` | 0x002C0EE0 | LR=0x00102188 |
| 0x001051DC | `BL` / `EB06EF3F` | 0x002C0EE0 | LR=0x001051E0 |
| 0x00106F00 | `B` / `EA06E7FD` | 0x002C0EFC | no cambia LR |
| 0x0010700C | `B` / `EA06E7BA` | 0x002C0EFC | no cambia LR |
| 0x002A8164 | `B` / `EA006364` | 0x002C0EFC | no cambia LR |
| 0x002C0F6C | `BL` / `EBFFFFE2` | 0x002C0EFC | LR=0x002C0F70 |
| 0x002C1260 | `BL` / `EBFFFF25` | 0x002C0EFC | LR=0x002C1264 |
| 0x002C1304 | `BL` / `EBFFFEFC` | 0x002C0EFC | LR=0x002C1308 |
| 0x002C5638 | `B` / `EAFFEE2F` | 0x002C0EFC | no cambia LR |

Los cuatro `B` no escriben un LR nuevo; la rutina en 0x002C0EFC retorna usando el LR guardado, por lo que son transferencias sin enlace/tail. Los tres `BL` fijan los LR de retorno de la tabla. El scan cubre immediate B/BL A32 alineado; no excluye indirect calls, referencias Thumb ni otros estados.

## Orden run-007 y alcance de las líneas HLE

El mismo log Azahar ordena los eventos en su reloj relativo:

- 2.246621: GDBStub recibe `Z0,2c0ee0,4`; 2.246628: responde `OK`.
- 2.246827: GDBStub recibe `c` (continue).
- 2.798544: Service.APT registra command=4, input_size=1, output_size=1.
- 2.801567: Service.APT registra command=7.
- 2.801648: Service.APT registra command=4, input_size=1, output_size=1.

Las dos entradas HLE command-4 aparecen después de que el GDBStub aceptó el breakpoint en 0x002C0EE0 y recibió continue. El capture JSON confirma breakpoint instalado/limpiado, attach a PID emulado `b`, detach, timeout y cero hits. En esa ventana no se observó ejecución en 0x002C0EE0 en el proceso depurado.

Las líneas Service.APT no incluyen PC, caller ni PID; el PID `b` y la proximidad temporal no vinculan las solicitudes con ese proceso. 0x002C0EFC es una ruta estática compatible con command 4, pero no fue instrumentada. Los datos no prueban que una o ambas solicitudes salieran de esa entrada ni identifican cuál de los nueve callsites las originó. Tampoco establecen el origen del burst de Run-028.

## Semántica de `Z1` en el GDB stub fijado

En `gdbstub.cpp` con el hash arriba indicado, `AddBreakpoint` mapea los `type_id` 0 y 1 (RSP `Z0` y `Z1`) ambos a `BreakpointType::Execute` (líneas 1752–1757). `CommitBreakpoint` guarda las instrucciones originales y, para Execute, escribe `btrap` o `btrap_thumb` mediante `Memory().WriteBlock` (líneas 1722–1731). Al quitar el breakpoint, `RemoveBreakpoint` restaura las instrucciones guardadas mediante otro `Memory().WriteBlock` (líneas 564–567). Por lo tanto `Z1` no es un breakpoint hardware en esta build; insertar y quitar tanto `Z0` como `Z1` modifica transitoriamente código guest. La recomendación previa de probar `Z1` y considerarlo read-only era incorrecta y queda retirada.

## Siguiente observación sin escrituras guest

No usar `Z0` ni `Z1` bajo un requisito estricto de cero escrituras guest. Proponer en un task posterior una traza diagnóstica host-side en la ejecución ARM privada: cuando el PC guest alcanza 0x002C0EFC, registrar solo PID emulado, PC, LR, SP y PC anterior (y, si hace falta, leer hasta dos palabras de stack), con máximo cuatro eventos y ocho segundos. Este hook debe observar estado, no escribir memoria/código guest ni inyectar entrada. LR identifica los tres retornos BL conocidos; PC anterior distingue los cuatro B si el backend puede exponerlo. Se necesita un mecanismo de instrumentación del backend que no use los breakpoints RSP del stub; verificar su viabilidad y gates offline en una asignación separada antes de cualquier runtime. Si tal hook read-only no está disponible, no hacer la captura con el stub actual bajo esa restricción.

Esta auditoría es de solo lectura sobre código y artefactos. No lancé Azahar/GDB, no accedí a saves/perfiles, y no generé evidencia runtime nueva.
