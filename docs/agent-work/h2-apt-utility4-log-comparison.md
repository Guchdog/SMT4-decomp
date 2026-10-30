# Comparación de logs: APT AppletUtility comando 4 (H2)

## Observación

Los logs HLE preservados muestran una diferencia marcada en llamadas al AppletUtility de APT:

| Captura | SHA-256 del log | Tamaño | command=0x4 | Intervalo observado |
|---|---|---:|---:|---|
| Run-017 | 987b60d6f3e7361eb59df6fa057ddb981fdb57310effa0d166d70f9b552ad245 | 12.337.017 B | 4 | 2,208011–3,152700 s |
| Run-028 | 08ac8e83968aa42b63a0f40de39ff3a42dc86a74bdf6e0308c1f665c05b80439 | 1.131.149 B | 6.452 | 1,817220–31,638805 s |

En Run-017 las cuatro llamadas son 2,208011, 2,211028, 2,708757 y 3,152700 s. En Run-028 las 6.452 llamadas abarcan 29,821585 s; la captura termina junto al límite de 30 s. En ambos logs también hay una llamada a command=0x7 (input_size=4, output_size=1). Las rutas y hashes se cotejaron con runtime-report.json de cada corrida.

La búsqueda contó líneas de AppletUtility:735 cuyo mensaje coincide exactamente con command=0X00000004, input_size=0X00000001, output_size=0X00000001. El resultado es evidencia del servicio HLE; por sí solo no identifica el caller guest, un bloqueo, la causa del desvío ni el significado de hardware del comando.

## Correlación estática acotada

Con code.bin fijado (base 0x00100000, SHA-256 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558), el bloque A32 0x002C0EE0..0x002C0F28 prepara r0=4, ceros en los demás argumentos y llama a 0x002B5A1C. Ese wrapper carga la cabecera APT AppletUtility 0x004B00C2, arma la petición IPC y ejecuta SVC #0x32. El escaneo de ramas A32 alineadas encontró dos BL directos a 0x002C0EE0: 0x00102184 y 0x001051DC. Sus continuaciones esperadas en LR son 0x00102188 y 0x001051E0. El helper y ambos callsites decodifican como ARM; los blancos de rama tienen bit Thumb despejado.

En el apt.cpp fijado de Azahar (SHA-256 d667babbd3f655c531a71f93cc6c6454147ae94420edf416a8b4aea1b864381f), AppletUtility construye una salida de output_size bytes inicializada en cero. Solo escribe true para el comando 0x6; para 0x4 esta build devuelve éxito HLE y un byte de salida cero. Esto caracteriza la implementación Azahar fijada, no el contrato de la consola ni la intención del juego.

## Siguiente captura propuesta

Una observación de entrada, máximo cuatro hits, en 0x002C0EE0 puede distinguir los dos callsites por LR sin volver al wrapper genérico SVC. Debe registrar PC, LR y registros, no escribir memoria guest ni inyectar queries, usar un perfil desechable/guardado fixture, loopback privado y un límite corto. Antes del lanzamiento el coordinador debe repetir los gates offline actuales. Ninguna captura nueva se autoriza por este informe.

## Límites y método

La lectura fue de solo lectura: no hubo build, emulador, debugger, acceso al guardado original ni modificación de perfil. Comandos usados: conteo de logs por regex del mensaje, búsqueda de 0x004B00C2, barrido de BL ARM alineados hacia 0x002C0EE0 y desensamblado Capstone de 0x002C0EE0..0x002C0F28, 0x002B5A1C..0x002B5AA0 y 0x0013B2A4..0x0013B320. Estos escaneos no prueban ausencia de callers indirectos ni mapean por sí mismos cada llamada de log con el helper.
