# ABI correction: 0x002BF6D0

La prueba inicial del candidato C++ sustituyó `0x002B0188` por un stub que aceptaba solo `group_id`. La inspección posterior del ARM mostró que `0x002BF6D0` conserva `node_index` en `r1` al llamar a `0x002B0188`; ese servicio salta a `0x00138B90`, que divide dicho índice por 1000 y avanza el manager en bloques de 32 bytes. El mock inicial ocultó este argumento y no cubrió índices que cruzan bloques.

Al tipar el servicio con ambos argumentos, Clang produce un cuerpo de 68 bytes para un span de 64. No se añadió código de cave ni se cambió el inventario; la sustitución C++ se retiró y se conservó el ARM original como `matching`. En ese momento, la prueba de `0x002B88C4` ejecutaba el resolver original y capturaba `(group_id, node_id)` en la frontera mockeada `0x002B0188`. Después se convirtió el resolver `0x002B0188`; su registro de función y la revisión independiente documentan la comparación con el resolver C++ instalado en la composición.

El informe antiguo `h2-bf6d0-manager-slot-convert/run001/report.json` solo acredita la hipótesis anterior bajo el stub incompleto; no es evidencia de promoción ni caller equivalence para el servicio real. Runtime no está probado.
