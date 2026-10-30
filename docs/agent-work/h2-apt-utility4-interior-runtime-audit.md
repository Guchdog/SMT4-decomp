# Auditoría independiente runtime: entrada APT Utility-4

**Packet:** `h2-apt-utility4-interior-runtime-audit`, run-001  
**Revisor:** `h3_read_return_review`  
**Alcance:** report/capture preservados, hashes, listing ARM fijado, runner y stub. No inicié Azahar/GDB ni accedí a saves/perfiles.

## Veredicto

La captura acredita que el stub respondió cuatro veces con PC `0x002C0EFC` durante un único proceso aislado y que el ciclo de limpieza declarado terminó. No acredita cuatro entradas APT distintas: los cuatro snapshots contienen el mismo PC, LR, todos los registros y stop reply, y el cliente envía `continue` otra vez sin avanzar una instrucción ni quitar el breakpoint entre hits. Que sean re-hits del mismo breakpoint es una explicación directa compatible con la traza, pero los datos no permiten asegurar que esa sea la causa única.

El LR observado `0x00103E84` es exactamente la continuación del `BL` estático en `0x00103E80`. El listing fijado da una ruta concreta hacia la entrada: `0x00103E80: BL 0x002C5624`; `0x002C5624` compara `r0` con cero, carga un valor a `r0`, marca un byte y hace `BEQ 0x002C563C`; cuando el `BEQ` no toma, la siguiente instrucción es `0x002C5638: B 0x002C0EFC`. En el caller, `r0` se fija a 1 inmediatamente antes de esa llamada. Esto es una explicación estática fuerte y compatible con LR, pero el runtime no detuvo en `0x002C5638` ni capturó el PC previo; por tanto no demuestra el origen dinámico de esos stops.

## Integridad del packet y gates

Recalculé los 15 SHA-256 del packet; todos coinciden. El reporte de captura conserva SHA-256 `712e97a9c0108d395402dda2e6c865c7c3f120bfea17d3520b115ba79bd749f2`; el log Azahar preservado tiene SHA-256 `fad6f05ac207c2f136b1b49322da0884d8a5f098d0ab097afe6852f5f9acb309` y 30,333 bytes.

La attestation declara `passed_with_warnings`; recomputé el hash de cada reporte gate y los cuatro coinciden con su manifest. `h2_differential`, `h2_caller_composition`, `h3_caller_composition` y `arm_thumb_interworking` figuran `passed`. Differential reporta 110/110 callbacks, 1,536/1,536 mapper cases y 4,096/4,096 fill-pair cases, pero incluye cuatro advertencias de source identity mismatch. Los caller reports registran 3/3 cases con negativo detectado y 8/8 assertions; el gate ARM/Thumb reporta 3 BL targets, 3 lock instruction sites y 7 dispatch caller instructions comprobados. La advertencia del gate está visible y no invalida por sí misma el hecho limitado de que la attestation se pasó; tampoco convierte esa evidencia offline en runtime equivalence.

## Stops y control de ejecución

El capture JSON declara cuatro hits con PC `0x002C0EFC`, LR `0x00103E84` y exactamente los mismos valores de `r0`–`r15` (`r0=0x0044e3b0`, `r1=1`, `r4=1`, `sp=0x0fffff00`, entre otros). También son iguales los stop replies. `capture_stop` es `max_hits_reached`.

El runner `collect_hits()` llama `continue_until_stop()` en cada vuelta y luego lee PC/registros; no manda `s`/single-step, no quita y vuelve a poner `Z0` por hit, y conserva el breakpoint hasta la limpieza final. La implementación fijada del GDB stub maneja `c` como continue y `s`/`S` por `HandleStep`; su `Z0` es breakpoint software `Execute`: `CommitBreakpoint` escribe `btrap` con `Memory().WriteBlock` y la retirada restaura bytes guardados con otro `WriteBlock`. Así que esta observación no es read-only respecto del código guest, aun cuando el reporte diga que no hubo paquetes `M/P/X` ni input lógico. Los cuatro hits son cuatro respuestas del stub en la ventana, no cuatro llamadas semánticamente independientes.

## Limpieza y preservación

El reporte documenta breakpoint insertado y retirado, attach y detach, `cleanup_errors=[]`, terminación del proceso y listener liberado: el listener inicial fue `127.0.0.1:61582`, PID 8060; luego no quedó listener. El stage propio fue eliminado. El hijo figura `terminated: true` con código de salida 1; esto es terminación observada, no salida graceful/limpia del emulador.

CCI: hash antes/después `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`, sin cambio. Ejecutable de origen: `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`, sin cambio. Los 12 archivos del profile seed y las dependencias runtime se reportan sin cambios. Fixture descartable y save staged: hash antes/después `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`, sin cambio. La attestation y el runtime report marcan `source_save_accessed:false` / `supplied_source_save_accessed:false`; el CCI quedó verificado por hash/alias y argv, y el reporte dice que su nombre no se validó en el log. Mi auditoría solo inspeccionó esos metadatos y no abrió el fixture ni perfil.

## Siguiente observación acotada

Preparar un packet independiente de un solo evento en el callsite `0x002C5638`, con el CCI/runner/base/helper y cuatro gates nuevamente fijados y verificados antes del launch. En el proceso aislado, instalar `Z0` solo allí y limitar la captura a un hit. Al detenerse, registrar PC/LR y quitar el breakpoint para restaurar la instrucción; luego, si el RSP single-step `s` se valida offline contra este stub, ejecutar exactamente una instrucción y leer el PC. `PC=0x002C0EFC` después de ese paso, junto con el stop previo en `0x002C5638` y LR, establecería que el tail branch fue ejecutado en esa observación. Si no se alcanza el callsite antes del deadline, informar cero hits sin inferir causa. Conservar el límite de una modificación guest temporal por software breakpoint, el cleanup completo, loopback/ownership, y terminación del proceso luego de la lectura. No intentar contar visitas distintas en un único breakpoint sin step-over.

## Evidencia

- Compilación: `not_run`.
- ARM differential: `not_run` en esta auditoría; se revisaron bytes/listing estáticos y gates offline existentes.
- Caller: `partial`; LR coincide con un callsite directo estático, pero no se observó el tail site ni caller PC.
- Runtime: `partial`; cuatro stops idénticos y cleanup reportado, sin conteo de llamadas distintas ni prueba de equivalencia funcional.
- H2 sigue abierto: la captura es un diagnóstico limitado y las cuatro source-identity warnings siguen visibles.
