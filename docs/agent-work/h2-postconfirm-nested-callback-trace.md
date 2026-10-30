# H2: traza del callback anidado tras confirmar

## Resultado

La captura pareada de la imagen original y la imagen H2 integrada observó la misma ruta durante la confirmación de los ajustes. Los 19 checkpoints comparados pasaron. Se observaron 20 retornos del callback anidado en cada ejecución y las trazas normalizadas coincidieron.

En cada evento, el handler exterior fue el ID 8; su callback anidado fue el ID 33. La dirección obtenida de la tabla y el destino real de BLX fueron `0x00221168`. El retorno bruto del callback fue `R0=0`; el retorno del handler exterior fue `R0=2`. El observador no escribió memoria del juego.

## Límites del resultado

Esto verifica paridad de la ruta guionizada, no la finalización funcional de H2. En ambos binarios, los 40 sondeos de readiness terminaron con `completed=false`; no hubo reentrada en la misma sesión. Los valores confirmados fueron 7/7/7. Tras cerrar y reiniciar el proceso, ambos mostraron 8/8/8, así que la captura no demuestra persistencia de los valores confirmados.

El recorrido automatizado establece la selección y sustituye temporalmente la consulta lógica por una respuesta determinista de un fotograma. No prueba la asignación de botones físicos ni la planificación de entrada. H2 queda abierto. Este resultado tampoco promociona una función ni afirma equivalencia de juego completo.

## Entorno y reproducibilidad

- Runtime: Azahar privado fijado por hash, enlazado al loopback; original y parche en perfiles desechables.
- CCI SHA-256: `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`.
- Imagen integrada SHA-256: `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`.
- IPS SHA-256: `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`.
- Manifiesto SHA-256: `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`.
- Azahar privado SHA-256: `1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682`.
- Runner de la captura, conservado en `source-tools-h2_postconfirm_nested_callback_trace.py`, SHA-256: `4c75031e0f2f7e499355a911a0dc3b7bb2198bfc91fd0d4137ebdac1c624ea57`.
- Los gates previos al lanzamiento pasaron con 32 entradas congeladas. Las pruebas focales se ejecutaron otra vez al cerrar este informe.
- Las semillas de perfil y los binarios fijados quedaron sin cambios; el directorio temporal de staging se eliminó. El archivo de guardado protegido no se leyó.

Después de la captura se corrigió el serializador de la atestación para quitar un sufijo literal `\n` que impedía analizar su JSON. Los bytes originales se conservaron en `prelaunch-attestation-raw-before-repair.txt`. La decisión de los gates ocurrió en proceso antes del lanzamiento; la corrección solo afecta el artefacto JSON guardado. La atestación corregida se puede analizar como JSON.

## Siguiente paso

Revisar el recorrido original de readiness y la ruta de confirmación para explicar por qué no hay finalización ni reentrada; diseñar una observación offline o RSP acotada que distinga una condición de estado faltante de una espera real. No marcar H2 completo hasta observar cierre y persistencia real.
