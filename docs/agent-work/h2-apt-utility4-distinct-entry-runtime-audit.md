# Auditoría independiente runtime: dos entradas en `0x002C0EFC`

## Resultado

El reporte runtime registra dos stops en `0x002C0EFC`, ambos en el hilo 1. En cada uno, marca retiro de `Z0`, paso al mismo hilo hasta `0x002C0F00`, LR/SP sin cambios y reinserción de `Z0` antes de continuar. La secuencia coincide con el runner fijado y la estática del `code.bin`. No hay transcripción RSP cruda por paquete; el orden en runtime está acreditado por los flags/per-hit replies del JSON y por el código del runner, no por un wire log independiente.

La captura fue parcial: configuró hasta 4 hits y un deadline RSP de 8 s, pero terminó por `capture_timeout` con 2 hits. El runner retiró y eliminó el breakpoint, hizo detach y reportó limpieza sin errores. Esto es evidencia de dos entradas instrumentadas en una ejecución; no cierra H2 ni prueba el comportamiento semántico de la función.

## Hits y LR

- Hit 1: PC `0x002C0EFC`; LR `0x00103E84`; SP `0x0FFFFF00`. El JSON deja la clasificación como `unresolved_possible_tail_or_indirect`. La imagen fijada confirma que el `BL` en `0x00103E80` llega a `0x002C5624`, y el `B` en `0x002C5638` llega a `0x002C0EFC`. Esto hace al LR compatible con la ruta de cola observada en una corrida separada; esta captura no observó `0x002C5638`, así que no demuestra que ese fuera su camino.
- Hit 2: PC `0x002C0EFC`; LR `0x002C1264`; SP `0x0FFFFE68`. El `BL` directo de `0x002C1260` llega a `0x002C0EFC`, por lo que la etiqueta `consistent_with_direct_bl` es adecuada. LR por sí solo sigue sin probar todo el historial del caller.

En ambos hits, el stop y el stop del paso son `T05` del hilo 1; el PC previo es `0x002C0EFC`, el posterior `0x002C0F00`, y los flags de LR/SP y selección del hilo son verdaderos. Los dos hits registran `breakpoint_reinserted=true`: el segundo también se reinsertó porque el límite era 4 y luego hubo otro continue hasta timeout. La limpieza final registra `breakpoint_cleared=true`, `detached=true` y cero errores.

## Hashes y puertas offline

Comprobé los hashes de los artefactos permitidos y sus pins: el capture JSON es `f197da2c…01d517`, el log preservado `942ef72e…d4beb`, la attestation `97b35a0f…dd1d2`, `code.bin` `1f98884f…aa558`, el runner distinct `dbb2c150…2311f5`, el runner compartido `e138aacf…65679` y el stub de Azahar `bb345fca…025d6`. Los cuatro reportes nombrados por la attestation coinciden con sus SHA-256 declarados. El detalle reproducible está en `checks/runtime-evidence-audit.json`.

La attestation marca las cuatro puertas como `passed`, pero el resumen es `passed_with_warnings`: H2 differential tiene cuatro avisos de identidad de fuente (tres mapper callsites y un fill source); H2 caller composition registra 3/3 casos y un control negativo detectado; H3 caller composition, 8/8 aserciones; y ARM/Thumb, 3 destinos BL, 3 sitios de lock y 7 instrucciones del caller. Por eso no presento las puertas como una ejecución sin avisos.

Leí el log permitido, confirmé su hash/tamaño (36.161 bytes) y comprobé independientemente que contiene el Program ID `00040000000E5C00`. El JSON también marca `title_id_in_log=true`. El claim `profile_path_in_log=true` queda como flag del JSON; no comparé ni abrí ruta alguna de perfil. El log no demuestra por sí solo listener, terminación ni eliminación del staging.

## Binding, limpieza y preservación: límites de lo comprobado

El JSON reporta binding `127.0.0.1:61582`, PID del listener igual al PID lanzado (`21876`), `listener_released=true`, proceso terminado/confirmado (`exit_code=1`) y staging eliminado. Son campos del reporte; no se adjuntó una salida netstat independiente ni una observación actual del proceso, así que no afirmo haber verificado esos estados fuera del JSON.

Los flags del JSON dicen: la fuente suministrada no fue accedida, no se stageó el fixture de save, el fixture desechable permaneció igual, el seed de perfil permaneció igual, el save staged no cambió y los archivos runtime permanecieron iguales. La attestation también dice `source_save_accessed=false`. No abrí ni calculé hashes de ninguna ruta de save o perfil —fuente o desechable—; esos puntos son solo flags declarados y no una verificación independiente de sus contenidos.

El reporte dice que no envió paquetes RSP explícitos `M/P/X` ni entradas lógicas. `Z0`/`z0` sí son breakpoints software que parchean temporalmente código guest; no equivale a “sin escrituras de memoria”.

## Siguiente acción

Conservar esta corrida como dos observaciones parciales, mantener la primera ruta como compatible pero sin atribución, y no usarla como cierre de H2. Para una conclusión sobre caller de la primera entrada haría falta observar el branch `0x002C5638` en esa misma ejecución o aportar una trazabilidad dinámica equivalente; la corrida tailstep separada sirve como contexto, no como historial de esta entrada.

No lancé Azahar/GDB, no ejecuté tests ni builds y no accedí a rutas de save o perfil.
