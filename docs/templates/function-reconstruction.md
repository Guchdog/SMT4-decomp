# Ficha de función — 0xDIRECCION

Copiar a `docs/function-records/0xDIRECCION.md` y completar los campos. Procedimiento:
[reconstrucción por función](../function-reconstruction-workflow.md).

## Identidad y estado

- Dirección, tamaño original y modo ARM/Thumb:
- Símbolo, fuente y marcador del ledger:
- Commit base y rama/worktree:
- Estado documental: investigada / reconstruida / probada_arm / probada_llamador /
  probada_juego / diferida / fallida.
- Coincidencia exacta de la propuesta: sí / no / sin comprobar.
- Fecha y fuente de la evidencia:

## Historial y selección

- Intentos previos y archivos consultados:
- Motivo para elegir/reabrir esta dirección:
- Hermana/familia y exclusiones relacionadas:
- Variantes intentadas y resultado; no repetir las mismas sin evidencia nueva:

## Contrato respaldado por evidencia

- Firma propuesta y evidencia de llamadores (direcciones):
- Argumentos enteros/VFP/stack, retorno y otros observables consumidos:
- Campos, offsets, anchuras, signo, alineación y almacenamiento accesible:
- Punteros/nulos, capacidad/rangos y vida útil:
- Aliasing permitido y prohibido, con motivo:
- Globales, llamadas, MMIO, hilos o excepciones:
- Registros que deben conservarse y convenciones especiales:
- Dudas y precondiciones todavía no demostradas:

## Reconstrucción y compilación

- Archivo/símbolo experimental y contrato de tipos:
- Revisión de comportamiento indefinido y justificación de `volatile` si se usa:
- Compilador, flags, versiones y hashes de fuente/objeto/referencia:
- Tamaños original/recompilado y diferencias observadas:
- Comandos exactos y códigos de salida:

## Pruebas de comportamiento

- Memoria/registros iniciales y preparación del runner:
- Casos límite, exhaustivos, aleatorios, semillas y conteos por corrida:
- Ramas, aliasing, alineación y efectos cubiertos:
- Retorno, memoria, ABI, accesos y flags que se comparan o se excluyen:
- Control negativo específico y error por el que debe ser rechazado:
- Contraejemplo mínimo si falla; datos/semilla suficientes para reproducirlo:
- Rutas locales únicas de informes, hashes y resultado de cada ejecución:
- Limitaciones: muestreo, backend compartido, soporte ausente y casos no cubiertos:

## Integración

- Caller(s), rango de instrucciones y continuaciones ejercitadas:
- Esquema de parche, destino, capacidad, relocaciones y entradas interiores:
- Verificación independiente de la imagen/IPS y sus hashes:
- Loader/emulador/consola, revisión y configuración si se probó el juego:
- Evidencia de ejecución de esta función y escenarios original/parche:
- Casos aún pendientes; escribir «no probado» si no hubo arranque real:

## Cierre

- Decisión y alcance exacto de la afirmación respaldada:
- Regresión del lote: pruebas ejecutadas/omitidas, auditoría y diff-check:
- Estado del wrapper, headers y ledger; cambios restaurados:
- Commit(s) y estado de publicación:
- Métrica: dirección única/bytes originales y nivel, sin doble conteo:
- Siguiente paso o condición concreta para reabrir un fallo:
