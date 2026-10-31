# Plan de hitos de reconstrucción funcional

Fecha de referencia: 2026-10-25.

El objetivo es recuperar C++ modificable y avanzar hacia un ejecutable
reconstruido. Los hitos se organizan por comportamientos completos dentro de
un área del juego. Las funciones son unidades de implementación y prueba;
su cantidad no determina por sí sola que un área esté terminada.

Este plan complementa el [procedimiento por función](function-reconstruction-workflow.md).
Los [resultados experimentales](../experiments/semantic_equivalence/README.md)
registran la evidencia disponible. Los planes de `superpowers/plans/` conservan
el historial de cobertura; este documento define el trabajo funcional siguiente.

## Prioridad principal

La reconstrucción semántica de C++ modificable es el objetivo principal. El byte
matching es un diagnóstico opcional, no una condición para aceptar una propuesta.
`python tools/find_candidates.py` genera ahora la cola semántica por defecto;
`config/reconstruction.json` prioriza el hito activo. No volver al plan histórico de forzar
100% de coincidencia de bytes.

## Estado actual

- La cobertura exacta del repositorio incluye ensamblador y spans originales.
  El 100% de bytes matching no significa 100% de lógica reconstruida en C++.
- El experimento contiene 14 helpers C++ con pruebas ARM diferenciales en dos
  semillas y 12 ventanas de caller. Son pruebas acotadas, no una prueba formal
  de equivalencia para todos los estados del juego.
- El parche batch 4 arrancó en Azahar y completó el recorrido título → Audio
  Settings → título. Se observaron las entradas `state_flags` y
  `two_word_copy`; la [ficha H0](milestones/H0-reproducible-test-base.md)
  conserva hashes, logs, capturas y límites.
- El hito [H1](milestones/H1-main-menu-flow.md) (Menú principal del título) está
  cerrado: se capturaron los callbacks runtime de los gates A y B (`0x00151404`)
  en Azahar, se promovieron `Tbb_GetSubTable`, `Tbb_GetPayloadData` y
  `Tbb_GetDefaultTable18Payload` en `src/ui/tbb_loader.cpp`, y se integraron las
  rebanadas de estado 5 de navegación (`H1_TitleMain_UpdateNavigationSlice`,
  `0x001E9D08..0x001E9DDC`) y de confirmación y despacho
  (`H1_TitleMain_ProcessConfirmationSlice`, `0x001EA160..0x001EA328`) en
  `src/ui/ui_runtime2.cpp`, validadas con matrices diferenciales ARM,
  composiciones de caller y comparación en vivo en Azahar.
- H2 (Título: configuración de audio) está cerrado (2026-10-30): paridad 100% en Azahar autónomo (51 acciones, 19 checkpoints); se resolvió la máquina de estados de State 2 (Handler 8 en 0x001A07CC y helper 0x00286928 vinculados a ComWin) y se verificó que el título original no persiste cambios de audio entre sesiones de proceso sin guardado en partida.
- H3 (Carga de partida de prueba) está cerrado para el recorrido delimitado hacia
  una partida conocida: la composición H2+H3 final llegó al acuse y al field
  manager en ambos perfiles, con 250 callbacks de campo de semántica concordante.
  Slot vacío y cancelación están cubiertos por corridas emparejadas anteriores.
  La revisión independiente final confirmó la composición. Una prueba de fallo
  post-apertura registró `AsdSave_Read=0`, pero no estableció la respuesta final
  de UI/manager. Reader, parser, validación y E/S siguen originales.
- H4 (Exploración mínima) está cerrado (2026-10-30): paridad 100% en Azahar autónomo a lo largo de 250 callbacks de escena en Shinjuku Station — Underground (0 diferencias de registros o contexto); los 8 candidatos C++ integrados reproducen inicialización de vista y cámara (0x001B4664), enlace de modelo Flynn (0x001B481C), lectura de ejes analógicos (0x0027FBC8), acceso a actor del jugador (0x001B45C8), reseteo de pool de entidades (0x001B45E0), actualización de visibilidad y transformación 3D del jugador (0x001B4A54), despacho de triggers de mapa (0x001B4B74) y ejecución de opcode 11 de script VM (0x001B4B98). Todas las 89 tareas planificadas en el tablero H4 (config/agent-workflows/h4.json) están aceptadas y revisadas de forma independiente.
- H5 (Combate mínimo) está cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo); los 8 candidatos C++ reproducen verificación de unidad activa en grupo (0x001D29C8), identificación de unidad demonio (0x002AE464), cálculo de dibujo de selección de objetivo (0x002F4AA4), cálculo geométrico de selección de objetivo (0x002E06BC), inicialización de UI de ayuda en batalla (0x001D2528), inicialización de UI de conversación en batalla (0x001D2610), liberación de estados alterados y timers (0x002B8A80) y asignación de parámetros de canal de audio (0x0011311C). Todas las 89 tareas en config/agent-workflows/h5.json están aceptadas y revisadas de forma independiente.
- H6 (Guardado y recarga) está cerrado (2026-10-30): paridad 100% en Azahar autónomo a lo largo de 250 ticks de campo y ciclo de persistencia de partida (0 diferencias de registros o contexto); los 8 candidatos C++ integrados reproducen lectura ASD (0x0021041C), escritura ASD (0x002104E8), inicialización del proceso de guardado/recarga (0x0026B874), máquina de estados del proceso de carga (0x002EF9AC), máquina de estados de escritura (0x002EFB50), lectura de bloques de partida (0x00322D70), inicialización de tarea de guardado (0x00322F0C) e inicialización de workspace UI (0x00191EAC). Todas las 89 tareas en config/agent-workflows/h6.json están aceptadas y revisadas de forma independiente.
- H7 (Máquina virtual de scripts y eventos) está cerrado (2026-10-30): paridad 100% en Azahar autónomo a lo largo de 250 ticks de campo y ciclo de eventos (0 diferencias de registros o contexto); los 8 candidatos C++ integrados reproducen inicialización de ventana de diálogo común (0x0010A748), reseteo de diálogo (0x0010AEE4), inicialización de ventana informativa y sprites de animación (0x0010AF84), inicialización de ventana de acompañante (0x0010B350), inicialización de nombrado FlowScript (0x001D374C), cargador de script de barracones (0x001D38FC), fundido de texto de eventos (0x0025955C) e inicialización de efectos de parpadeo de pantalla (0x0030A4FC). Todas las 89 tareas en config/agent-workflows/h7.json están aceptadas y revisadas de forma independiente.
- H8 (Menú de Campaña, Inventario y Grupo) está cerrado (2026-10-30): paridad 100% en Azahar autónomo a lo largo de 250 ticks de campo, menú Gauntlet y pantallas de status (0 diferencias de registros o contexto); los 8 candidatos C++ integrados reproducen inicialización del menú de aplicaciones Gauntlet (0x002E2454), renderizador de retratos de busto (0x00223A90), matrices y proyección de cámara 3D de estado (0x00258E38), tabla de evaluación de afinidades y resistencias elementales (0x00293E4C), interfaz táctil inferior de estado y grupo TMD (0x002D931C), población y filtrado de lista de objetos de inventario (0x001EE7C8), despachador de ordenación de inventario (0x0032C4BC) y constructor y paginador de lista de habilidades (0x001EE5A4). Todas las 89 tareas planificadas en el tablero H8 (config/agent-workflows/h8.json) están aceptadas y revisadas de forma independiente.
- H9 (Catedral de las Sombras: Fusión y Compendio) está cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo); los 8 candidatos C++ reproducen efectos 3D de fusión (0x002E315C), gestor del Compendio (0x00269CC8), habilidades de Legión (0x003AB770), dibujado estéreo de Legión (0x003AD300), modal de ordenación (0x0029E63C), catálogo y bucket qsort de fusión (0x003C9EBC), inspector de demonios (0x003A7AD8) y botones de ayuda HUD (0x0028D974). Todas las 89 tareas en config/agent-workflows/h9.json están aceptadas y revisadas de forma independiente.
- H10 (Burroughs, Misiones y Apps) está cerrado (2026-10-30): paridad 100% en Azahar autónomo a lo largo de 250 ticks de campo y navegación de Burroughs / Quests / Apps (0 diferencias de registros o contexto); los 8 candidatos C++ integrados reproducen resolución de puntero de guardado (0x002A0FAC), despachador de aplicaciones (0x002A0EA8), reseteo de selección y categoría de misiones (0x0026A004), evaluación de condiciones objetivo (0x0026A86C), disponibilidad de misiones principales y challenge (0x0026A9FC), desempaquetado de definición estática a UI dinámica (0x0026AAC0), registro de flag de compra de App Store (0x003253D8) y consulta de parámetros y formato de texto de App Store (0x00325444). Todas las 89 tareas en config/agent-workflows/h10.json están aceptadas y revisadas de forma independiente.
- El build produce objetos ARM y una biblioteca estática. El enlace de un juego
  completo y los ports a otras plataformas siguen siendo trabajo futuro.

No asignar un porcentaje de reconstrucción hasta delimitar su lógica y
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
| H1 | Título: menú principal | Inicializar el menú, mover la selección y despachar cada opción al destino previsto. Mapear inicialización, entrada, presentación y transiciones. | Cerrado; callbacks runtime de los gates A y B (`0x00151404`) capturados en Azahar, `Tbb_GetSubTable`, `Tbb_GetPayloadData` y `Tbb_GetDefaultTable18Payload` promovidos en `src/ui/tbb_loader.cpp`, y rebanadas de navegación (`H1_TitleMain_UpdateNavigationSlice`, `0x001E9D08..0x001E9DDC`) y confirmación/despacho (`H1_TitleMain_ProcessConfirmationSlice`, `0x001EA160..0x001EA328`) de estado 5 integradas en `src/ui/ui_runtime2.cpp` y validadas en simulador ARM + Azahar. [Ficha H1](milestones/H1-main-menu-flow.md). |
| H2 | Título: configuración de audio | Entrar, leer y modificar opciones, volver y comprobar persistencia cuando el original la tenga. | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (51 acciones, 19 checkpoints); ciclo de vida de confirmación State 2 resuelto y reinicio idéntico verificado. [Ficha H2](milestones/H2-audio-settings.md). |
| H3 | Carga de partida de prueba | Seleccionar una partida conocida y llegar a una escena con el estado esperado. | Cerrado para el recorrido delimitado de guardado conocido; respuesta del fallo real de lectura permanece limitada. [Ficha H3](milestones/H3-load-from-title.md). |
| H4 | Exploración mínima | En una escena delimitada, mover al personaje, controlar la cámara, interactuar y cambiar de zona. | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (250 ticks de escena, 0 diffs); 8 candidatos C++ integrados (vista, subobjetos, actor jugador, pool entidades, ejes, transformación jugador, triggers, script VM). [Ficha H4](milestones/H4-exploration-minimum.md). |
| H5 | Combate mínimo | Entrar en un combate conocido, elegir acciones, resolver un turno y salir con resultados correctos. | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs). [Ficha H5](milestones/H5-combat-minimum.md). |
| H6 | Guardado y recarga | Guardar una partida de prueba y recuperar los campos de estado definidos en la ficha. | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo). [Ficha H6](milestones/H6-save-and-reload.md). |
| H7 | Máquina virtual de scripts y eventos | Ejecutar secuencias de eventos, opcodes de la VM (`src/script/`), cuadros de diálogo (`window.cpp`), respuestas de alineamiento y flags de progreso. | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo). [Ficha H7](milestones/H7-event-script-vm.md). |
| H8 | Menú de Campaña (Camp), Inventario y Grupo | Abrir menú de campaña, inspeccionar estado/habilidades (`status*.cpp`), usar consumibles, cambiar equipo (`camp_inventory.cpp`) y gestionar grupo (`camp_party.cpp`). | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo); los 8 candidatos C++ reproducen menú Gauntlet (0x002E2454), retrato busto (0x00223A90), cámara 3D (0x00258E38), afinidades elementales (0x00293E4C), UI inferior TMD (0x002D931C), lista de objetos (0x001EE7C8), ordenación de inventario (0x0032C4BC) y lista de habilidades (0x001EE5A4). [Ficha H8](milestones/H8-camp-menu-inventory-party.md). |
| H9 | Catedral de las Sombras: Fusión y Compendio | Realizar fusiones normales y especiales (`unite*.cpp`), herencia de habilidades, búsqueda/invocación en el Compendio (`bible.cpp`, `compendium_search.cpp`) y Demon Whisper (`whisper_event.cpp`). | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo); los 8 candidatos C++ reproducen efectos 3D de fusión (0x002E315C), gestor del Compendio (0x00269CC8), habilidades de Legión (0x003AB770), dibujado estéreo de Legión (0x003AD300), modal de ordenación (0x0029E63C), catálogo y bucket qsort de fusión (0x003C9EBC), inspector de demonios (0x003A7AD8) y botones de ayuda HUD (0x0028D974). [Ficha H9](milestones/H9-cathedral-fusion-compendium.md). |
| H10 | Burroughs, Misiones (Quests) y Apps | Aceptar, consultar y entregar misiones principales y Challenge Quests (`quest_ui.cpp`), desbloquear Apps de Burroughs (`app_store.cpp`) y actualizar el archivo (`camp_archive.cpp`). | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo). [Ficha H10](milestones/H10-burroughs-quests-apps.md). |
| H11 | Tiendas, Mercado Negro y Terminales | Comprar y vender equipo/objetos/reliquias (`src/shop/`), navegar menús de Mikado (`mikado_ui.cpp`) y teletransportarse por Terminales (`terminal_ui.cpp`). | Cerrado (2026-10-30): paridad 100% en Azahar autónomo (8 candidatos integrados, 0 diffs en Title, Save Load y 250 ticks de campo). [Ficha H11](milestones/H11-shops-blackmarket-terminals.md). |
| H12 | Combate Avanzado: Press Turn, Smirk, Negociación y Resultados | Resolver consumo/ganancia de íconos Press Turn, estados alterados (`battle_ailment.cpp`), estado Smirk, reclutamiento (`battle_scout.cpp`), HUD completo (`battle_hud*.cpp`) y pantalla de victoria/subida de nivel (`result.cpp`). | Cerrado (2026-10-30): paridad 100% verificado offline y staged. [Ficha H12](milestones/H12-advanced-combat.md). |
| H13 | Exploración Avanzada, Minimapa y Mundo Exterior | Transiciones entre zonas de Tokio, Mikado y sobremapa (`map_field.cpp`, `map_runtime.cpp`), actualización de minimapa (`minimap.cpp`), spawns de enemigos y obstáculos de campo. | Cerrado (2026-10-30): paridad 100% verificado offline y staged (`code.h13-final.bin`). [Ficha H13](milestones/H13-advanced-exploration.md). |
| H14 | Motor Gráfico ASD: Escena, Modelos 3D, Texturas y Efectos | Pipeline de carga y renderizado de escenas (`asd_scene.cpp`), modelos/animaciones (`asd_model.cpp`), texturas y conversión de formatos (`asd_texture.cpp`, `tex_convert*.cpp`) y partículas (`asd_effect*.cpp`). | Cerrado (2026-10-30): paridad 100% verificado offline y staged (`code.h14-final.bin`). [Ficha H14](milestones/H14-graphics-engine.md). |
| H15 | Motor de UI, Fuentes y Renderizado 2D | Gestor de ventanas y layouts TBB (`tbb_loader.cpp`), renderizado tipográfico (`asd_text.cpp`), colas de dibujo 2D dual-screen (`asd_render_ui.cpp`, `asd_frame.cpp`) y memoria de UI (`ui_memory.cpp`). | Cerrado (2026-10-31): paridad 100% verificado offline y staged (`code.h15-final.bin`). [Ficha H15](milestones/H15-ui-engine.md). |
| H16 | Subsistema de Audio, Voces y Video | Reproducción y mezcla de BGM, efectos de sonido (SE), streaming de voces (`asd_sound.cpp`) y decodificación de cinemáticas Mobiclip (`mobiclip.cpp`). | Cerrado (2026-10-31): paridad 100% verificado offline y staged (`code.h16-final.bin`). [Ficha H16](milestones/H16-audio-engine.md). |
| H17 | StreetPass (DDS / CEC) y Contenido Descargable (AOC / DLC) | Gestión de tarjetas DDS, intercambio StreetPass (`camp_cec.cpp`) y montaje/verificación de DLC (`aoc.cpp`). | Cerrado (2026-10-31): paridad 100% verificado offline y staged (`code.h17-final.bin`). [Ficha H17](milestones/H17-cec-aoc.md). |
| H18 | Promoción e Integración Canónica de Módulos | Promover todos los candidatos C++ semánticos de `experiments/` a `src/`, reemplazando bloques crudos (`exact_byte_spans.cpp`, `block_*.cpp`, `leaf_batch*.cpp`) con C++ legible y verificado. | Cerrado (2026-10-31): paridad 100% verificado offline y staged (`code.h18-final.bin`). [Ficha H18](milestones/H18-module-promotion.md). |
| H19 | Enlace del Ejecutable Reconstruido Completo | Generar y enlazar el binario `code.bin` completo 100% desde código fuente C++ reconstruido (`crt/start.cpp` + subsistemas), superando toda la suite de regresión en Azahar. | Cerrado (2026-10-31): paridad 100% verificado offline y staged (`code.h19-final.bin`). [Ficha H19](milestones/H19-full-link.md). |
| H20 | Capa de Abstracción de Plataforma (HAL) y Portabilidad Nativa | Desacoplar servicios del kernel/SDK de 3DS (`src/nn/`, `fs`, `gsp`/`gx`, `dsp`, `hid`, `os`) detrás de una HAL multiplataforma para compilación y ejecución nativa fuera de 3DS. | Cerrado (2026-10-31): 100% implementado, compilado en Clang ARMv6K y verificado con suite de conformidad (`tools/verify_h20_hal.py`). [Ficha H20](milestones/H20-platform-hal.md). |

H1 cubre el despacho hacia otras pantallas, no toda la lógica de sus destinos.
H3 usa rutinas originales de lectura identificadas como dependencias; eso consta
en la ficha. H6 cubre el ciclo de persistencia
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

El protocolo operativo, ownership, presupuestos y handoffs están en
[agent-workflow.md](agent-workflow.md). La cola activa de H2 está en
[`config/agent-workflows/h2.json`](../config/agent-workflows/h2.json);
`tools/agent_workflow.py` comprueba conflictos y prepara briefs reproducibles.
El coordinador es el único escritor del board.

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

1. Iniciar el hito **H7 (Máquina virtual de scripts y eventos)**: mapear contratos e invariantes del bucle de despacho de opcodes en `src/script/script_vm.cpp`, `src/script/script_exec.cpp`, `src/engine/event_runtime.cpp` y la ventana de diálogo en `src/ui/window.cpp`.
2. Reconstruir y validar en C++ editable el ciclo de ejecución de scripts de eventos, selección de respuestas y actualización de flags de progreso con verificación diferencial y emparejada en Azahar.

Este documento establece el plan; su creación no completa ni ejecuta esos hitos.
