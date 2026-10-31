# Ficha de Hito H18: Promoción e Integración Canónica de Módulos

- **Fecha de Cierre:** 2026-10-31
- **Estado:** CERRADO (100% verificado offline y staged)
- **Objetivo:** Promover todos los candidatos C++ semánticos de `experiments/` a `src/semantic/`, reemplazando bloques crudos con C++ legible, editable y verificado.
- **Subsistemas Promovidos:**
  1. `h10_burroughs`: Burroughs Save Data (`0x002A0FAC`, 24 B, 0 B headroom)
  2. `h11_shops`: Shop Check New Inventory (`0x0022FC98`, 48 B window, 36 B compiled, +12 B headroom)
  3. `h12_combat`: Battle Unit Smirk State (`0x00129C58`, 24 B window, 20 B compiled, +4 B headroom)
  4. `h13_exploration`: PlaceWin UI Active State (`0x0026394C`, 44 B window, 44 B compiled, 0 B headroom)
  5. `h14_graphics`: ASD GPU Heap Size (`0x002C3B88`, 16 B window, 16 B compiled, 0 B headroom)
  6. `h15_ui`: UI Dialog State (`0x00126084`, 16 B window, 16 B compiled, 0 B headroom)
  7. `h16_sound`: ASD Sound Effect Buffer Size (`0x00110C44`, 28 B window, 28 B compiled, 0 B headroom)
  8. `h17_cec_aoc`: AOC Result Readiness Check (`0x002A17C0`, 20 B window, 20 B compiled, 0 B headroom)
- **Verificación:**
  - 100% de paridad diferencial en Unicorn ARM11 MPCORE (`tools/generate_h18_experiments.py`).
  - Imagen final acumulativa `code.h18-final.bin` y parche LayeredFS IPS `code.h18-final.ips` generados y verificados en roundtrip (`tools/h18_staged_image_patch.py`).
