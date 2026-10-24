# Plan de hitos de reconstrucción funcional

Fecha de referencia: 2026-10-24.

El objetivo es recuperar C++ modificable y avanzar hacia un ejecutable
reconstruido. Los hitos se organizan por comportamientos completos dentro de
un área del juego. Las funciones son unidades de implementación y prueba;
su cantidad no determina por sí sola que un área esté terminada.

Este plan complementa el [procedimiento por función](function-reconstruction-workflow.md).
Los [resultados experimentales](../experiments/semantic_equivalence/README.md)
registran la evidencia disponible. Los planes de `superpowers/plans/` conservan
el historial de cobertura; este documento define el trabajo funcional siguiente.

## Estado actual

- La cobertura exacta del repositorio incluye ensamblador y spans originales.
  El 100% de bytes matching no significa 100% de lógica reconstruida en C++.
- El experimento contiene 14 helpers C++ con pruebas ARM diferenciales en dos
  semillas y 11 ventanas de caller. Son pruebas acotadas, no una prueba formal
  de equivalencia para todos los estados del juego.
- El parche batch 4 arrancó en Azahar y completó el recorrido título → Audio
  Settings → título. Se observaron las entradas `state_flags` y
  `two_word_copy`; la [ficha H0](milestones/H0-reproducible-test-base.md)
  conserva hashes, logs, capturas y límites.
- El mapa estático del menú principal y los criterios de H1 están en
  [la ficha H1](milestones/H1-main-menu-flow.md). Ya se auditaron límites de
  callbacks y contratos TBB, y se corrigió el parser Python con pruebas
  sintéticas. El runner recibió un validador aparte para blobs ARM con ramas
  locales y literales internos. H1 sigue activo: falta medir navegación, ejecutar
  un modo diferencial específico para más getters TBB, resolver estado inicial
  y reconstruir lógica C++ activa; tres propuestas TBB pasaron 426 comparaciones
  sintéticas (70 payload, 71 subtabla y 72 row-count por semilla), más 14 con el
  `TitleTable.tbb` extraído; los controles negativos dirigidos también se
  detectaron en las dos semillas. El
  recorrido de Audio Settings sólo es evidencia parcial de H0.
- El build produce objetos ARM y una biblioteca estática. El enlace de un juego
  completo y los ports a otras plataformas siguen siendo trabajo futuro.

No asignar un porcentaje de reconstrucción al menú hasta delimitar su lógica y
sus dependencias. Las cifras anteriores describen dimensiones distintas.

## Organización y orden de trabajo

Usar tres niveles: **área → hito funcional → lotes de funciones**. Elegir las
funciones por su contribución al hito activo, incluyendo dependencias de otros
subsistemas. Registrar por qué una tarea de infraestructura desbloquea ese hito.

Mantener un hito principal activo. El siguiente puede investigarse en paralelo,
pero los lotes deben converger en un recorrido verificable. El orden de la tabla
es inicial y puede cambiar si el mapa de dependencias lo justifica; registrar
el motivo del cambio. No estimar fechas mediante funciones por noche.

| ID | Área e hito | Criterio de aceptación funcional | Estado inicial |
| --- | --- | --- | --- |
| H0 | Base de pruebas reproducible | Regenerar e identificar el parche, comprobar su carga en Azahar y registrar un recorrido repetible con las entradas ejecutadas y sus límites. | Cerrado; batch 4 llegó al título y Audio Settings. Dos entradas dieron hit. [Ficha H0](milestones/H0-reproducible-test-base.md). |
| H1 | Título: menú principal | Inicializar el menú, mover la selección y despachar cada opción al destino previsto. Mapear inicialización, entrada, presentación y transiciones. | Activo; mapa y parser documentados; tres getters TBB pasaron 426 comparaciones ARM sintéticas y 14 con el asset real. Pendientes navegación, integración TBB y reconstrucción C++ activa. [Ficha H1](milestones/H1-main-menu-flow.md). |
| H2 | Título: configuración de audio | Entrar, leer y modificar opciones, volver y comprobar persistencia cuando el original la tenga. | Pendiente. |
| H3 | Carga de partida de prueba | Seleccionar una partida conocida y llegar a una escena con el estado esperado. | Pendiente. |
| H4 | Exploración mínima | En una escena delimitada, mover al personaje, controlar la cámara, interactuar y cambiar de zona. | Pendiente. |
| H5 | Combate mínimo | Entrar en un combate conocido, elegir acciones, resolver un turno y salir con resultados correctos. | Pendiente. |
| H6 | Guardado y recarga | Guardar una partida de prueba y recuperar los campos de estado definidos en la ficha. | Pendiente. |

H1 cubre el despacho hacia otras pantallas, no toda la lógica de sus destinos.
H3 puede usar inicialmente rutinas originales de lectura identificadas como
dependencias; eso debe constar en el resultado. H6 cubre el ciclo de persistencia
del escenario elegido, no todos los formatos y casos de guardado del juego.
Las pruebas que escriban opciones o partidas usarán un perfil de prueba y copias
conocidas, con comparación del estado antes y después.

Esta primera secuencia valida el método y recorre sistemas importantes del juego.
No constituye el plan completo de un port: después se necesitarán más escenas,
variantes de combate, scripts, recursos, sistemas restantes, enlace del ejecutable
y sustitución de servicios específicos de 3DS. Abrir esos hitos cuando sus
dependencias y criterios de aceptación puedan definirse con evidencia.

## Dos resultados que se registran por separado

1. **Recorrido integrado validado:** la versión parcheada supera las pruebas del
   escenario frente al original. Puede seguir dependiendo de funciones originales.
2. **Lógica del alcance reconstruida:** las funciones que implementan el alcance
   acordado tienen C++ y evidencia por función y por integración. Las dependencias
   originales restantes están enumeradas y justificadas fuera de ese alcance.

Una función original dentro del alcance mantiene pendiente el segundo resultado.
Si queda una llamada indirecta o dependencia sin resolver, registrar el pendiente
en lugar de declarar cobertura completa. Un hit del monitor sólo demuestra que
se alcanzó una entrada; no verifica su comportamiento ni cierra un hito.

## Ficha obligatoria por hito

Crear `docs/milestones/HN-nombre.md` al iniciar cada hito usando esta estructura:

```markdown
# HN — Nombre

Estado: pendiente / mapeando / implementando / validando / cerrado
Responsable de integración:
Revisión base y fecha:

## Resultado esperado
Comportamiento observable y escenario concreto.

## Alcance y exclusiones
Pantallas, estados y transiciones cubiertos; límites acordados.

## Dependencias
Dirección/símbolo, función en el recorrido, estado de reconstrucción,
dependencias originales e indirectas pendientes. Enlaces a fichas por función.

## Pruebas de aceptación
Estado inicial, acciones, resultados esperados, campos observados,
comparación con el original y procedimiento de reinicio del escenario.

## Lotes y responsables
Objetivo de cada lote, archivos asignados y orden de integración.

## Evidencia
Revisión/fuentes, hashes de referencia y parche, toolchain, comandos,
semillas, informes, registros del emulador y condiciones de reproducción.
Mantener imágenes del juego, partidas y artefactos privados fuera de Git.

## Pendientes y cierre
Fallos, dependencias sin resolver y límites de las pruebas.
Recorrido integrado validado: sí/no, con evidencia.
Lógica del alcance reconstruida: sí/no, con evidencia.
Próxima acción concreta.
```

Definir las pruebas antes de implementar. Incluir alternativas y bordes relevantes
al escenario: volver/cancelar, repetir una transición, índices límite o estados
vacíos cuando correspondan. Para estado aleatorio o dependiente del tiempo,
registrar cómo se controla o qué comparación se acepta. Capturar únicamente
el estado necesario para contrastar el comportamiento.

## Trabajo con subagentes

- **Mapa y contratos:** identificar flujo, dependencias, llamadas indirectas,
  entradas y salidas; proponer funciones que desbloqueen el hito.
- **Implementación:** reconstruir un lote con archivos asignados y seguir las
  fichas y el procedimiento de validación por función.
- **Pruebas y revisión:** preparar casos, controles negativos y revisión
  independiente de contratos y resultados.
- **Integración principal:** coordinar interfaces, integrar cambios, ejecutar
  el recorrido y actualizar el estado del hito con evidencia.

Asignar archivos distintos a quienes implementan en paralelo. Cuando varios
lotes necesitan cambiar el runner o una interfaz compartida, designar un único
responsable e integrar esos cambios antes de regenerar la evidencia dependiente.
Cada entrega debe incluir archivos cambiados, pruebas, resultados y pendientes.
Los subagentes que terminan pueden revisar otros lotes o estudiar el siguiente
hito. No cerrar un hito sólo porque todos los subagentes terminaron sus tareas.

## Cierre y seguimiento

Cerrar un hito cuando ambos resultados anteriores estén respaldados, las pruebas
de aceptación pasen, no queden fallos conocidos dentro del alcance y la ficha
permita reproducir el resultado. Aplicar la regresión prevista por el
procedimiento por función y actualizar README, ficha y registro de cambios.
Repetir pruebas si cambia una dependencia que invalida su evidencia.

Informar del progreso con escenarios verificados, lógica reconstruida,
dependencias originales y pendientes. El número de funciones y bytes sirve como
medida auxiliar. Mantener separado el ledger exacto del avance semántico.

## Próxima sesión

1. Completar H1-A: resolver caller/origen del estado inicial y correspondencia
   de triggers con entradas físicas, sin confirmar rutas que alteren partidas.
2. Preparar una ventana segura de caller para los tres getters. El payload,
   subtable y row count ya tienen pruebas aisladas sintéticas y del asset real;
   conectar al recorrido sólo tras confirmar su participación real. Las fichas
   H1 describen contratos y casos.

Este documento establece el plan; su creación no completa ni ejecuta esos hitos.
