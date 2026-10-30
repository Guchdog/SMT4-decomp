# Revisión independiente: sondeo de un paso en el salto APT Utility-4

**Task:** h2-apt-utility4-tailstep-probe-review, run-003  
**Alcance:** runner, pruebas, packet congelado y código GDB stub fijado. Solo lectura de fuentes y validación offline; no inicié Azahar/GDB y no accedí a perfiles ni guardados.

## Veredicto

La captura normal tiene una secuencia coherente: exige un stop T05 con thread id, selecciona ese hilo para leer registros, verifica PC en 0x002C5638, quita Z0 antes de s, fija Hc al mismo hilo y acepta el paso solo si vuelve T05 con el mismo hilo, PC 0x002C0EFC y LR/SP preservados. El contrato estático confirma la instrucción B de 0x002C5638 a 0x002C0EFC.

**Recomiendo mantener el runtime en espera hasta cerrar explícitamente la ruta de respuesta perdida de Z0.** En esa ruta, el runner puede enviar D y desconectar antes de terminar al proceso aislado; el stub reanuda el proceso al desprenderse. La terminación posterior contiene la ejecución, pero no demuestra que el breakpoint se restaurara antes del resume.

## Evidencia revisada

- El hash de los 20 inputs congelados del packet coincide; detalle en input-hash-audit.json.
- python -m unittest tests.test_h2_apt_utility4_tailstep_probe -v: 6 pruebas, exit 0. Son pruebas offline con fake RSP más el check del code.bin fijado.
- Hashes de fuentes principales:
- tools/h2_apt_utility4_tailstep_probe.py: 61137fc707d616280a6d6cad5cf184f7230117f9abf5376b730466b9351a072b
- tests/test_h2_apt_utility4_tailstep_probe.py: dd6df80fa15438e5404da36deb92b2b835acb86f8edd508053afcccd4416d177
- tools/h2_apt_utility4_caller_probe.py: 10043a4062f11e24329fd4c2ff3b693230707784d1a21b8a458595f11e0e6a14
- build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src/core/gdbstub/gdbstub.cpp: bb345fcaca1e09f41a5d5f6941a4eef5d98e0b0257b15aa98ce993c0a22025d6
- build/agent-work/H2-semantic/h2-apt-utility4-tailstep-probe/run-002/task.json: 15071cc3c4dda04512e2a9880e9c153a7900a2d735b822a241421e134904929f
- build/agent-work/H2-semantic/h2-apt-utility4-tailstep-probe/run-002/handoff.json: 45733824dbca03c0d60795725acabbf0ceb908a2940d27e6b7f03d7476578c4a
- build/agent-work/H2-semantic/h2-apt-utility4-tailstep-probe/run-002/checks/unit-tests.txt: b36b81078eef7415aa76f9af84a9b0b54de7356b3f92e2546d10fe4f52bbc1de
- build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/reference/code.bin: 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558

## Contrato y control de hilo

verify_tail_contract() primero delega a interior.verify_interior_entry(), que fija la identidad del code.bin y el inventario de entradas, y luego comprueba las palabras ARM 0xE3A00001 en 0x00103E78, 0xEB0705E7 en 0x00103E80, 0xE3500000 en 0x002C5624, 0x0A000000 en 0x002C5634 y 0xEAFFEE2F en 0x002C5638. El BL en 0x00103E80 apunta a 0x002C5624; el B incondicional apunta a 0x002C0EFC. La ruta anterior sigue condicionada: la evidencia estática no demuestra que este caller alcance el branch en una sesión concreta.

stop_thread() requiere T05 (SIGTRAP) y extrae el campo thread hexadecimal. El runner envía Hg<id> antes de leer registros y Hc<id> antes de s. El stub acepta Hc solo para un thread existente; HandleStep() resuelve ese id y ResumeThreads() pone en step solo ese hilo. OnSingleStepComplete() genera SIGTRAP para ese hilo. El fake cubre thread distinto, PC destino incorrecto, ausencia de id y señal distinta. PC antes/después, LR y SP se verifican; no se afirma que todos los registros se comparen después del paso.

## Hallazgo de limpieza: respuesta Z0 ambigua

La sonda retira Z0 explícitamente antes de s (runner lines 70–83). El stub implementa Z0 con escritura temporal de la instrucción Bkpt y z0 restaura los bytes originales (GDB stub lines 1706–1740 y 553–574). El cleanup heredado vuelve a enviar z0; el stub responde OK incluso si el breakpoint ya no está, así que el segundo retiro es idempotente cuando el primero tuvo éxito.

Pero capture_session() manda D después de intentar el retiro, y DetachAndRestartServer() quita el modo unschedule de GDB y reanuda el proceso (base runner lines 594–613; GDB stub lines 1068–1082 y 2006–2009). Si la respuesta a z0 se pierde y el retiro tampoco queda confirmado, el proceso puede reanudar con la instrucción de breakpoint puesta hasta que execute() termina el hijo aislado. Si se pierde la respuesta de Z0 de inserción, breakpoint_set sigue false, el cleanup no intenta z0 y D igualmente reanuda. En ambos casos la contención final por terminación no equivale a restauración confirmada antes de resume.

La prueba actual cubre pérdida de respuesta de inserción y de s. En el primer caso comprueba que no se intenta z0 y que sí se envían D/cierre; en el segundo comprueba el z0 de la sonda más el z0 redundante de cleanup, D y cierre. No existe un caso de respuesta z0 perdida (incluido “comando aplicado pero respuesta perdida”), y el fake no modela el efecto de D de reanudar ni el orden con la terminación del proceso.

También hay una limitación de reporte: si ya existe un error original y fallan los intentos de cleanup, capture_session() vuelve a lanzar el error original antes de elevar cleanup_errors; el llamador pierde la lista concreta de fallos RSP, aunque execute() todavía intente terminar el proceso y revise el listener.

## Recomendación concreta

Antes de una captura runtime, endurecer el camino de error: ante respuesta ambigua de Z0/z0, evitar D/cierre que reanude el proceso antes de la terminación aislada, o registrar explícitamente ese resume como estado no restaurado y garantizar que el resultado quede failed/no promovible. Añadir un fake-RSP para z0 aplicado sin respuesta y para retiro no confirmado, y verificar que el proceso se termina antes de desconectar/reanudar o que la incertidumbre se registra. Agregar los errores de cleanup al reporte final en vez de ocultarlos detrás del error original. Después, regenerar packet/gates si cambia el runner y volver a revisar antes del runtime.

## Límites

- No se ejecutaron emulator, GDB, ni differential/caller runners.
- No se leyeron ni modificaron perfiles o guardados.
- El resultado revisa implementación y fake tests; no prueba comportamiento dinámico del guest ni equivalencia funcional.
- Evidencia: compiled not_run; ARM differential not_run; caller partial (contrato/caller estáticos revisados); runtime not_run.

## Revisión correctiva run-004: limpieza fatal del sondeo tailstep

**Task:** h2-apt-utility4-tailstep-probe-review, run-004  
**Alcance:** source/read paths fijados, GDB stub y pruebas offline. No inicié Azahar/GDB ni accedí a perfiles o guardados.

### Veredicto

El cambio corrige el riesgo principal de run-003 para errores de Z0/z0/s: execute pasa on_fatal; capture_session termina y verifica el proceso antes de D o de cerrar el socket. Si falla esa terminación, conserva ambos errores y deja el socket abierto. Las 9 pruebas fake-RSP pasan.

**Recomiendo continuar con una captura runtime acotada, aceptando explícitamente la limitación de D.** En la ruta de D, el z0 anterior ya tuvo respuesta OK: la instrucción guest se restauró antes de intentar desprenderse. Si se pierde la respuesta D, el stub podría haber reanudado el proceso; el callback lo termina cuando expira/falla la petición. La ventana afecta al proceso y a su perfil/save de staging desechables, no al save fuente. Un fallo o ambigüedad de D debe quedar como ejecución fallida y no promover evidencia de captura limpia.

### Verificación de código

- En tools/h2_apt_utility4_caller_probe.py, execute crea stop_child_on_rsp_error() y lo pasa como on_fatal a capture_session().
- Si capture_session ya tiene un error original, entra a fatal_cleanup y llama al callback antes de intentar breakpoint cleanup, D o cierre de socket.
- Si falla el z0 normal de cleanup o falla D, captura el error y llama on_fatal antes de seguir. Si la terminación falla, child_stopped queda false y no se cierra el socket; el error fatal y el de cleanup se concatenan.
- execute() hace un segundo intento de terminación en su finally y preserva stage si no puede confirmar que el proceso paró.
- El GDB stub confirma el límite de D: HandleCommand envía OK y llama DetachAndRestartServer; esa función quita el modo GDB-unschedule y reanuda. Por eso una respuesta D perdida puede seguir a una reanudación aunque el callback termine el proceso inmediatamente después de detectar el timeout.
- En el camino normal, z0 fue confirmado antes de D. El stub restaura la instrucción guardada durante z0; si ya no existe breakpoint, RemoveBreakpoint no escribe memoria y el handler devuelve OK.

### Pruebas y límite de cobertura

- python -m unittest tests.test_h2_apt_utility4_tailstep_probe -v: 9 pruebas, exit 0.
- Las nuevas pruebas fuerzan errores Z0, z0 durante el paso, s y z0 de cleanup; comprueban que el callback precede D/cierre, que no se manda D en fatal cleanup, y que una terminación fallida mantiene abierto el socket y conserva el error original más el de terminación.
- La prueba production_fatal_callback llama capture_session directamente con un callback fake; no cruza execute(). El código de execute sí conecta el callback en la línea correspondiente, pero la suite no protege esa integración. El EndToEndTimeoutCleanup previo recorre execute en el caso de timeout recuperable, no en el fatal path. Recomiendo añadir un test execute-level antes de promocionar el runner; la falta de ese test no invalida el orden visible en source ni la contención runtime.
- D límite residual: si el comando D fue aplicado pero no llega la respuesta, el proceso puede ejecutar durante el timeout de cleanup antes de que on_fatal lo mate. En este caso el breakpoint ya tuvo z0 confirmado y el escenario usa copias desechables. El resultado debe fallar cerrado si no se confirma D/cleanup.

### Evidencia e identidades

Los 20 inputs SHA-256 del packet run-004 coinciden; detalle en input-hash-audit.json. El test log está en focused-tests.txt.

- tools/h2_apt_utility4_tailstep_probe.py: 61137fc707d616280a6d6cad5cf184f7230117f9abf5376b730466b9351a072b
- tests/test_h2_apt_utility4_tailstep_probe.py: 7f2540e5f56f4fed6fc01a40d1dcea1610068083dff662a2f6db06c4ede48d9f
- tools/h2_apt_utility4_caller_probe.py: 15ef6ffcc51c24df5ab428188d0fd4afed9060ace5657d22752dcacc551db2c3
- tests/test_h2_apt_utility4_caller_probe.py: 7e95296b8fd40248ca30c31490173881cfa2f955231fb5f918f37ffa3e2719e9
- build/agent-work/H2-semantic/h2-private-azahar-source/azahar/src/core/gdbstub/gdbstub.cpp: bb345fcaca1e09f41a5d5f6941a4eef5d98e0b0257b15aa98ce993c0a22025d6
- build/agent-work/H2-semantic/h2-apt-utility4-tailstep-probe/run-003/task.json: a0e4bfd046f12957bedd0871370b755a3d99cdefe30b364189a5bcf25dda1fef
- build/agent-work/H2-semantic/h2-apt-utility4-tailstep-probe/run-003/handoff.json: e1ca3a4d93fe760ac076218e057574e46617c46dc92c0d7fb63b7f3f090ed2ec
- build/agent-work/H2-semantic/h2-apt-utility4-tailstep-probe/run-003/checks/unit-tests.txt: 7a4fbf7cda297b4697d3ff1941a32af2cb44bfe29edcd616a42e125600b54db4
- build/agent-work/H2-semantic/h2-apt-utility4-caller-probe-runtime/reference/code.bin: 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558

### Límites

- Compilación: not_run; ARM differential: not_run; caller: partial (lectura estática de contrato y runner); runtime: not_run.
- No se tocaron Azahar/GDB, perfiles, saves ni el board.
- Las pruebas usan fake RSP y no ejercitan el GDB stub real ni la latencia de respuesta perdida; se inspeccionó el código del stub fijado.
