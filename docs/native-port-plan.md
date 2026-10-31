# Plan de reconstrucción integral para un port nativo

Estado: planificación; la auditoría inicial y los recuentos verificables están pendientes.

## Objetivo y alcance

Dar cuenta de todas las funciones de la revisión CTR-P-AMXE v0.1.0 en C++ editable o mediante sustituciones portables con comportamiento respaldado por evidencia. El inventario actual contiene 10.959 funciones y ocho segmentos de bytes; son una línea de partida, no una garantía de límites correctos ni una medida de lógica reconstruida. Revisar también entradas interiores, código indirecto y segmentos sin clasificar. Mantener trazabilidad cuando se unan, dividan o reclasifiquen entradas. La identidad binaria ARM es diagnóstico opcional.

Un port nativo completo requiere que los recorridos soportados no ejecuten código ARM original. La reconstrucción integral exige además resolver las entradas no cubiertas por esos recorridos. Una sustitución de biblioteca o servicio debe registrar qué direcciones cubre y cómo se verificó su contrato; no eliminar funciones del inventario por considerarlas triviales o inalcanzables.

## Estado inicial y límites

La cobertura exacta de bytes incluye envoltorios y datos ARM originales. El inventario semántico cuenta definiciones y enlaces estáticos, no equivalencia. H19 genera una imagen ARM compuesta que conserva funciones originales; H20 prueba módulos HAL aislados en host. La compilación CMake principal solo admite ARM. La promoción semántica sigue siendo incremental. Los resultados de escenarios y los cierres de tareas se interpretan dentro de su alcance documentado, no como prueba de cobertura del juego entero.

## Fases y entregables

### P0 — Auditoría y línea base

Cruzar `config/functions.csv`, código, candidatos, evidencias y símbolos con la revisión original fijada. Registrar por dirección: límites y modo, familia, llamadores y dependencias conocidas, forma de implementación, estado de validación, evidencia y dudas. Investigar solapamientos, entradas interiores, llamadas indirectas y las ocho regiones crudas. Conservar la identidad y los hashes de los insumos, sin versionar archivos privados. Crear un informe reproducible con recuentos separados y fecha. Revisar contradicciones documentales sin alterar registros históricos de coincidencia exacta.

Salida: inventario completo y reproducible con pendientes explícitos; aún no se infiere equivalencia de presencia estática.

### P1 — Clasificación y herramientas de lotes

Clasificar como lógica de juego, motor compartido, biblioteca/runtime, servicio 3DS, envoltorio/duplicado o desconocido. Generar para familias paquetes con desensamblado, referencias, llamadas, estructuras propuestas, candidatos y pruebas existentes. Usar `python tools/find_candidates.py` para descubrimiento y `--include-existing-candidates` para integración. Las propuestas generadas son borradores que requieren revisión; conservar correspondencia por dirección. Preparar harnesses reutilizables con inicialización, comparación de registros y memoria, casos límite y mutantes.

Salida: un primer lote representativo traducido, revisado y medido de extremo a extremo, más una cola priorizada por dependencias y coste real. No fijar estimaciones globales hasta medirla.

### P2 — Fundamentos y dependencias compartidas

Reconstruir familias de memoria, cadenas, matemáticas, contenedores, gestión de tareas, archivos y recursos según sus contratos y llamadores. Consolidar tipos y estructuras comunes antes de expandir familias dependientes. Identificar bibliotecas y servicios de plataforma y registrar sus sustituciones portables por dirección y contrato.

Salida: módulos compartidos integrados y pruebas diferenciales y de composición para sus contratos documentados.

### P3 — Bucle principal, scripts y presentación

Reconstruir inicialización, despachadores, máquina de scripts y sistemas de recursos, gráficos, UI, audio y vídeo por familias coherentes. Conectar las interfaces de plataforma al código real; especificar los límites de renderizado, entrada, sincronización y formatos 3DS. Las implementaciones de prueba de la HAL no son por sí mismas backends completos del juego.

Salida: componentes integrados con llamadas y efectos observables contrastados; dependencias y rutas pendientes registradas.

### P4 — Lógica de juego y recorridos nativos

Avanzar por título, carga, exploración, combate, resultados, guardado, menús, fusión y misiones. Traducir también las dependencias transversales de cada recorrido y continuar el barrido de familias restantes. Preparar un target nativo en CMake y un backend inicial para Windows x86-64, con Linux y macOS posteriores. Comprobar punteros de 32/64 bits, alineación, endianidad, serialización y temporización. Los recursos proceden de la copia privada del usuario.

Salida: recorridos progresivos reproducibles, comparados con el original, sin ejecución ARM original en los recorridos declarados nativos. Un recorrido funcional no cierra automáticamente todas las funciones ni ramas de su subsistema.

### P5 — Cobertura integral y cierre

Revisar todas las entradas y segmentos pendientes, incluidas rutas excepcionales, servicios opcionales, callbacks indirectos y código no observado. Cada entrada debe vincularse a C++ integrado y validado o a una sustitución portable con contrato y evidencia; las fronteras corregidas mantienen trazabilidad. Documentar imposibilidad o incertidumbre como pendiente, nunca como completado. Ejecutar regresiones por subsistema, escenarios integrados y pruebas de portabilidad por plataforma.

Salida: inventario reconciliado, sin dependencias originales para los recorridos soportados, con pruebas reproducibles, límites y problemas conocidos. La cobertura completa de lógica y la de escenarios se presentan por separado.

## Flujo de cada lote

1. Seleccionar una familia o rebanada coherente con dependencias y archivos exclusivos; conservar cambios existentes y congelar insumos de prueba.
2. Recuperar contratos, ABI, tipos, valores de retorno, efectos, ramas y llamadores. Registrar hipótesis y llamadas indirectas sin resolver.
3. Implementar C++ legible o una sustitución portable justificada. Evitar cambios cuyo único objetivo sea igualar instrucciones.
4. Compilar y comparar con el original en casos específicos, límites y controles negativos; comprobar composición con llamadores. Registrar semillas, hashes, fallos y dominio cubierto.
5. Obtener revisión independiente, promover el código sustentado y ejecutar una regresión de integración por lote. Repetir evidencia invalidada por cambios compartidos.
6. Antes de lanzar el emulador, comprobar interworking ARM/Thumb y superar las pruebas diferenciales y de composición offline. Si hace falta runtime, usar Azahar privado y scripts RSP autónomos según `docs/emulator-testing-guide.md`.

El coordinador mantiene el board, interfaces y cierre de lote; los trabajadores tienen ownership exclusivo y presupuestos de compilación compartidos conforme a `docs/agent-workflow.md`. No crear cadenas de tareas para cambios menores. Un estado `accepted`, un enlace estático a una prueba o un hit de monitor no certifica equivalencia.

## Medición y reporte

El README debe reflejar una línea base fechada y enlazar informes reproducibles. Mantener dimensiones separadas: inventario y regiones; clasificadas; C++ integrado; contratos diferenciales validados; sustituciones nativas validadas; escenarios nativos; desconocidas y validación parcial. No sumar recuentos con ámbitos distintos ni convertir cobertura de bytes en porcentaje de traducción. No declarar 0 validaciones cuando no exista una auditoría: usar «pendiente de auditoría».

## Próxima acción

Ejecutar P0 en el checkout semántico, preservar los cambios existentes y crear el informe reproducible de línea base. Seleccionar después un lote representativo con dependencias y pruebas existentes para medir el coste real de P1.
