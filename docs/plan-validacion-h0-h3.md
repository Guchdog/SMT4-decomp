# Plan de validación y reconstrucción H0–H3

## Objetivo

Establecer qué comportamiento de H0–H3 está respaldado por evidencia, qué lógica tiene C++ editable integrado y qué partes siguen dependiendo del original. La aceptación de una función cubre un contrato y un dominio explícitos; las pruebas no establecen corrección absoluta para todos los estados posibles.

H4 permanece fuera de este plan y en pausa por indicación del usuario.

## Orden de trabajo

### 1. Inventario y alcance

- Enumerar las funciones y fragmentos que participan en los recorridos H0–H3. Para cada uno, registrar dirección, función, llamadores, dependencias originales, candidato C++, integración y evidencia disponible.
- Clasificar cada elemento como pendiente de contrato, candidato, validado de forma limitada o integrado y validado. Anotar explícitamente los límites y la revisión independiente.
- Tratar el inventario de definiciones experimentales como punto de partida, no como un recuento de funciones completas o aceptadas. No sumar dimensiones distintas para producir un porcentaje de equivalencia.

### 2. H0 — Base reproducible

- Identificar mediante hashes la referencia, el compilador, el parche y el entorno de prueba. Reproducir el arranque y el recorrido título → Audio Settings → título.
- Confirmar que el parche se aplica y que se alcanzan los reemplazos previstos. Un hit por sí solo no demuestra que la función sea correcta.
- Registrar comandos, resultados, artefactos, cobertura y límites. Conservar la evidencia anterior y explicar cualquier diferencia de entorno.

### 3. H1 — Menú principal

- Mapear dentro del alcance la inicialización, navegación, confirmación y despacho, junto con sus llamadores y dependencias originales.
- Revisar los contratos y la evidencia diferencial, de composición y runtime de los reemplazos ya integrados, incluidos los helpers TBB y las rebanadas de navegación y confirmación.
- Completar las lagunas de los recorridos acordados y comparar original y parche con el mismo estado inicial y las mismas entradas. Registrar por separado las rutas y dependencias no cubiertas.

### 4. H2 — Configuración de audio

- La ficha H2 y el reporte respaldan 12 checkpoints. Se repitió la suite sobre el compuesto H2 final + H3 y pasaron los 12. Se corrigió el mensaje del runner que imprimía el denominador obsoleto `/11`; la corrección solo afecta el texto del resultado.
- La suite cubre los checkpoints enumerados en la ficha H2. Persistencia y servicios originales mantienen los límites ya documentados.

### 5. H3 — Carga desde el título

- Completar la revisión independiente de la composición final H2+H3 y reconciliar la ficha con sus trazas. Mantener separados el fallo de apertura y el fallo real durante la lectura; ninguno demuestra por sí solo un error visible.
- Ya se provocó un fallo real después de abrir, truncando solo la copia aislada en el breakpoint posterior a apertura: `AsdSave_Read` devolvió `r0=0` en `0x00210478`; el control intacto devolvió `r0=1`. El validador devolvió `r0=1`, pero no se capturaron acuse, entrada al field manager ni error visible. La revisión independiente final confirmó estos resultados y sus límites.
- Lector, parser, validación y E/S siguen siendo dependencias originales; esta observación no las reconstruye.
- Solo se alteraron copias aisladas. El archivo fuente mantuvo su SHA-256 antes y después.

### 6. Validación y promoción por función

Para cada lote coherente que avance H0–H3:

1. Recuperar el contrato: tipos, ABI, retorno, efectos en memoria, ramas y comportamiento de los llamadores.
2. Implementar C++ legible y compilarlo para el ABI requerido.
3. Comparar el original fijado y el C++ compilado con casos normales, límites, errores y controles negativos o mutaciones detectables. Registrar fallos, dependencias y dominios no probados.
4. Comparar la composición con llamadores reales y revisar ARM/Thumb e interworking cuando corresponda.
5. Obtener revisión independiente de código, pruebas y evidencia antes de promover. Resolver hallazgos o dejar la función parcial con su motivo.
6. Integrar el reemplazo de manera reproducible, ejecutar las regresiones afectadas y actualizar su registro y clasificación sin llamar `matching` a bytes diferentes.

### 7. Regresión conjunta y cierre

- Congelar las entradas relevantes, generar la imagen integrada y repetir una vez la regresión pertinente de H0–H3 contra original y parche con estados iniciales equivalentes.
- Antes de cualquier lanzamiento de Azahar, superar las comprobaciones ARM/Thumb y los runners offline diferenciales y de composición aplicables. Usar el Azahar privado con GDB en loopback y scripts autónomos, conforme a `docs/emulator-testing-guide.md`.
- Registrar hashes, comandos, resultados, controles, diferencias, fallos y dependencias originales. Mantener imágenes del juego, partidas y artefactos privados fuera de Git.
- Por cada hito, responder por separado: **¿recorrido integrado validado?** y **¿lógica del alcance reconstruida en C++?** Una dependencia original dentro del alcance deja pendiente la segunda respuesta.
- Entregar un recuento respaldado por fichas de funciones aceptadas, parciales y pendientes. No presentar presencia de candidatos, hits o coincidencia de bytes como prueba de equivalencia del juego completo.

## Evidencia de partida

- [Estado funcional](functional-status.md) y [plan de hitos](reconstruction-milestones.md).
- [Inventario de candidatos](semantic-inventory.md).
- Fichas [H0](milestones/H0-reproducible-test-base.md), [H1](milestones/H1-main-menu-flow.md), [H2](milestones/H2-audio-settings.md) y [H3](milestones/H3-load-from-title.md).
- [Flujo de trabajo de agentes](agent-workflow.md) y [guía de pruebas en emulador](emulator-testing-guide.md).
