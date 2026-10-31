# Ficha de Hito H19: Enlace del Ejecutable Reconstruido Completo

- **Fecha de Cierre:** 2026-10-31
- **Estado:** CERRADO (100% verificado offline y staged)
- **Objetivo:** Generar y enlazar el binario `code.bin` completo desde código fuente C++ reconstruido (`src/crt/start.cpp` + subsistemas promovidos H0..H18), garantizando la integridad de bootstrap y la coherencia de enlace global.
- **Componentes de Enlace Clave:**
  1. `__start`: Vector de entrada del ejecutable (`0x00100000`, 36 B, despacho ordenado de CRT y subsistemas)
  2. `__init_bss`: Inicialización y limpieza a cero de la sección BSS (`0x00100024`, 36 B, rango `0x00477000..0x004EFE34`, 495,156 B)
  3. Cobertura completa de subsistemas semánticos integrados (Burroughs, Tiendas, Combate, Exploración, Gráficos ASD, UI, Sonido ASD, CEC StreetPass y AOC DLC).
- **Verificación:**
  - 100% de paridad diferencial en Unicorn ARM11 MPCORE (`tools/h19_crt_start_experiment.py`).
  - Imagen final acumulativa `code.h19-final.bin` y parche LayeredFS IPS `code.h19-final.ips` generados y verificados en roundtrip (`tools/h19_staged_image_patch.py`).
