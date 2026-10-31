# Ficha de Hito H19: Enlace del Ejecutable Reconstruido Completo

- **Fecha de Cierre:** 2026-10-31
- **Estado:** COMPLETADO Y CERRADO (2026-10-31)
- **Objetivo y Alcance del Hito:** Establecer la infraestructura de enlace y síntesis de imagen para el ejecutable completo (`code.bin`), integrando el vector de entrada y bootstrap CRT (`__start` y `__init_bss`) en `src/crt/start.cpp`, la composición acumulativa con los 8 subsistemas canónicos promovidos de H10 a H18, y la generación de parches LayeredFS IPS con verificación de roundtrip.
- **Componentes de Enlace e Integración Clave:**
  1. `__start`: Vector de entrada del ejecutable (`0x00100000`, 36 B, despacho ordenado del CRT de Atlus/Nintendo) en `src/crt/start.cpp`.
  2. `__init_bss`: Inicialización y limpieza a cero de la sección BSS (`0x00100024`, 36 B, rango `0x00477000..0x004EFE34`, 495,156 B) en `src/crt/start.cpp`.
  3. Staging y síntesis acumulativa: Pipeline de composición (`tools/h19_staged_image_patch.py`) que genera la imagen integral `code.h19-final.bin` (3,633,152 bytes) y el parche LayeredFS `code.h19-final.ips` (30,736 bytes).
  4. Módulos canónicos integrados: Burroughs (`h10`), Tiendas (`h11`), Combate (`h12`), Exploración (`h13`), Gráficos ASD (`h14`), Motor UI (`h15`), Motor de Sonido (`h16`), StreetPass y DLC (`h17`).
- **Verificación Autónoma y Evidencia:**
  - Compilación limpia con Clang ARMv6K de todos los módulos (`tools/build_h19_all.py`).
  - 100% de paridad diferencial en Unicorn ARM11 MPCORE (`tools/h19_crt_start_experiment.py`) sobre los 495,156 bytes de BSS y registros R0..R2.
  - Prueba de mutación automatizada: mutación en el bucle de BSS detectada y rechazada eficazmente.
  - Verificación de roundtrip exacto del parche IPS contra la imagen base y original.
  - Suite unificada autónoma `tools/verify_h19_full_link.py` ejecutada con 100% de éxito en sus 5 fases.
  - Tablero de workflow de agentes `config/agent-workflows/h19.json` con las 20 tareas planificadas aceptadas y revisadas independientemente.
- **Límites Técnicos y Relación con Hitos Posteriores:**
  - H19 valida y cierra la arquitectura global de enlace, el punto de entrada oficial (`0x00100000`), el ciclo de vida de BSS y la generación reproducible de la imagen ejecutable completa y parches LayeredFS.
  - La sustitución progresiva de las funciones binarias remanentes continúa realizándose de forma incremental en los hitos posteriores (H18 / H20 en adelante).
