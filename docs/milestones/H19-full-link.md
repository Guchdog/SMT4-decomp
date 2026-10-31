# Ficha de Hito H19: Enlace del Ejecutable Reconstruido Completo

- **Fecha de Evaluación:** 2026-10-31
- **Estado:** ABIERTO / EN PROGRESO (Staging incremental de bootstrap CRT; enlace integral del 100% pendiente)
- **Objetivo Documentado:** Generar y enlazar el binario `code.bin` completo desde código fuente C++ reconstruido (`src/crt/start.cpp` + todos los subsistemas promovidos), garantizando la integridad de bootstrap y la sustitución completa de los binarios originales.
- **Avance Real y Componentes Integrados:**
  1. `__start`: Vector de entrada del ejecutable (`0x00100000`, 36 B, despacho ordenado de CRT y subsistemas) en `src/crt/start.cpp`.
  2. `__init_bss`: Inicialización y limpieza a cero de la sección BSS (`0x00100024`, 36 B, rango `0x00477000..0x004EFE34`, 495,156 B) en `src/crt/start.cpp`.
  3. Composición incremental de módulos semánticos promovidos (Burroughs, Tiendas, Combate, Exploración, Gráficos ASD, UI, Sonido ASD, CEC StreetPass y AOC DLC).
- **Límites Técnicos y Discrepancias Identificadas:**
  - El generador de imagen (`tools/h19_staged_image_patch.py`) parte de la imagen acumulativa `code.h18-final.bin` y sustituye únicamente dos ventanas de código de bootstrap (`__start` y `__init_bss`). No enlaza el 100% del ejecutable desde C++ reconstruido.
  - La imagen generada `code.h19-final.bin` tiene 3,633,152 bytes y difiere del `code.bin` original en solo 19,053 bytes (~0.5% del ejecutable; ~99.5% sigue siendo código binario original extraído).
  - La prueba diferencial (`tools/h19_crt_start_experiment.py`) cubre exclusivamente el arranque temprano del CRT y la puesta a cero de BSS, no la ejecución ni enlace completo del juego.
- **Criterio para Cierre Futuro:**
  - Reemplazar progresivamente el resto de las secciones de código hasta que la totalidad de los módulos ejecutables provengan de código C++ reconstruido y compilado en el pipeline de enlace canónico.
