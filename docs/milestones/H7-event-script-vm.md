# H7 — Máquina virtual de scripts y eventos (Script VM and Event Runtime)

Estado: cerrado (2026-10-30)
Responsable de integración: Altair (Coordinator)
Revisión base y fecha: codex/semantic-equivalence-experiment, 2026-10-30

## Resultado alcanzado

Máquina virtual de scripts y subsistemas de tiempo de ejecución de eventos en Shin Megami Tensei IV reconstruidos en C++ legible y verificable:
1. Inicialización de ventana de diálogo común (`ComWin_Init`, `0x0010A748`): 384 B / 504 B ventana (+120 B margen).
2. Reseteo y limpieza de ventana de diálogo (`ComWin_Reset`, `0x0010AEE4`): 84 B / 84 B ventana (+0 B margen, optimización `-Oz`).
3. Inicialización de ventana informativa y animación de sprites (`InfoWin_Init`, `0x0010AF84`): 388 B / 560 B ventana (+172 B margen).
4. Inicialización de ventana de acompañante/interacción (`GuestWin_Init`, `0x0010B350`): 340 B / 448 B ventana (+108 B margen).
5. Inicialización de evento de nombrado FlowScript (`nameMain_Init`, `0x001D374C`): 324 B / 408 B ventana (+84 B margen).
6. Cargador y despachador de eventos de barracones (`onesRoom_Init`, `0x001D38FC`): 288 B / 392 B ventana (+104 B margen).
7. Ejecutor de comandos de fundido de texto de eventos (`eventCommand_func_0025955c`, `0x0025955C`): 340 B / 516 B ventana (+176 B margen).
8. Inicializador de efectos visuales de parpadeo de pantalla (`EventEffect_func_0030a4fc`, `0x0030A4FC`): 248 B / 504 B ventana (+256 B margen).

El escenario compara la ejecución bit a bit de estados, estructuras de datos, offsets y efectos de memoria entre el código original y el reemplazo integrado reconstruido en C++, validado de forma autónoma en el emulador Azahar con 0 regresiones.

## Candidatos reconstruidos e integrados

| Función / VMA | Ventana Orig | Candidato C++ | Margen NOP | Archivo Fuente |
|---|---|---|---|---|
| `0x0010A748` | 504 B | 384 B | +120 B | `experiments/semantic_equivalence/h7_ui_comwin_init_candidate.cpp` |
| `0x0010AEE4` | 84 B | 84 B | +0 B | `experiments/semantic_equivalence/h7_ui_comwin_reset_candidate.cpp` |
| `0x0010AF84` | 560 B | 388 B | +172 B | `experiments/semantic_equivalence/h7_ui_infowin_init_candidate.cpp` |
| `0x0010B350` | 448 B | 340 B | +108 B | `experiments/semantic_equivalence/h7_ui_guestwin_init_candidate.cpp` |
| `0x001D374C` | 408 B | 324 B | +84 B | `experiments/semantic_equivalence/h7_script_namemain_init_candidate.cpp` |
| `0x001D38FC` | 392 B | 288 B | +104 B | `experiments/semantic_equivalence/h7_script_onesroom_init_candidate.cpp` |
| `0x0025955C` | 516 B | 340 B | +176 B | `experiments/semantic_equivalence/h7_script_eventcmd_fade_candidate.cpp` |
| `0x0030A4FC` | 504 B | 248 B | +256 B | `experiments/semantic_equivalence/h7_script_eventeffect_init_candidate.cpp` |
| **Total** | **3,416 B** | **2,396 B** | **+1,020 B** | 8 subsistemas de eventos y VM |

## Artefactos y Huellas Criptográficas

- **Imagen binaria final compuesta:** `build/agent-work/H7-semantic/h7-integrated-stage/code.h7-final.bin`
  - SHA-256: `477ae5941b1163f56533b74128635e6deb22ddf796d4f4c18d65bdb02ddda3f8`
- **Parche LayeredFS IPS:** `build/agent-work/H7-semantic/h7-integrated-stage/code.h7-final.ips`
  - SHA-256: `08eee6b3b42e166baf0e99afea7083a780a63f564bc2204706c8e09ad83206de` (15,926 bytes)
  - Verificación Round-trip IPS: PASSED
- **Partida de prueba fija:** `sdds4game1.sav`
  - SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`

## Pruebas de aceptación superadas

1. **Compilación Clang ARMv6K:** Todos los candidatos compilan en C++ reproducible sin desbordar el tamaño de la ventana binaria original (+1,020 B de margen libre total).
2. **Pruebas Diferenciales Unicorn:** Simulación ARM bit a bit verificando registros de retorno, efectos de memoria, argumentos a funciones auxiliares y sensibilidad ante mutaciones (100% aprobado en los 8 componentes).
3. **Staging Compuesto:** Mod IPS generado y verificado contra `code.h6-final.bin` con ida y vuelta exacta.
4. **Verificación Autónoma en Azahar:** Paridad idéntica en arranque, título, carga de partida y 250 callbacks de exploración de campo sin regresiones.
