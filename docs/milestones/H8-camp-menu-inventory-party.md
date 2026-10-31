# H8 — Menú de Campaña (Camp), Inventario y Grupo (Camp Menu, Inventory, and Party Management)

Estado: cerrado (2026-10-30)
Responsable de integración: Altair (Coordinator)
Revisión base y fecha: codex/semantic-equivalence-experiment, 2026-10-30

## Resultado alcanzado

Menú de campaña, subsistema de inventario de objetos y gestión de grupo en Shin Megami Tensei IV reconstruidos en C++ legible y verificable:
1. Inicialización del menú de aplicaciones de Gauntlet (`GauntletAppMenu_Init`, `0x002E2454`): 268 B / 764 B ventana (+496 B margen).
2. Inicialización del renderizador de retratos de busto (`StatusBustUp_Init`, `0x00223A90`): 184 B / 248 B ventana (+64 B margen).
3. Configuración de matrices y proyección de cámara 3D de estado (`StatusCamera_Init`, `0x00258E38`): 360 B / 480 B ventana (+120 B margen).
4. Tabla de evaluación de afinidades y resistencias elementales (`Status_UpdateAffinityTable`, `0x00293E4C`): 316 B / 520 B ventana (+204 B margen).
5. Inicialización de interfaz táctil inferior de estado y grupo (`StatusDown_Init`, `0x002D931C`): 440 B / 764 B ventana (+324 B margen).
6. Población y filtrado de lista de objetos de inventario (`StatusDown_PopulateItemList`, `0x001EE7C8`): 324 B / 384 B ventana (+60 B margen).
7. Despachador de ordenación de inventario (`StatusDown_SortItemList`, `0x0032C4BC`): 208 B / 372 B ventana (+164 B margen).
8. Constructor y paginador de lista de habilidades (`StatusDown_PopulateSkillList`, `0x001EE5A4`): 368 B / 548 B ventana (+180 B margen).

El escenario compara la ejecución bit a bit de estados, estructuras de datos, offsets y efectos de memoria entre el código original y el reemplazo integrado reconstruido en C++, validado de forma autónoma en el emulador Azahar con 0 regresiones.

## Candidatos reconstruidos e integrados

| Función / VMA | Ventana Orig | Candidato C++ | Margen NOP | Archivo Fuente |
|---|---|---|---|---|
| `0x002E2454` | 764 B | 268 B | +496 B | `experiments/semantic_equivalence/h8_camp_gauntletmenu_init_candidate.cpp` |
| `0x00223A90` | 248 B | 184 B | +64 B | `experiments/semantic_equivalence/h8_ui_status_bustup_candidate.cpp` |
| `0x00258E38` | 480 B | 360 B | +120 B | `experiments/semantic_equivalence/h8_ui_status_camera_candidate.cpp` |
| `0x00293E4C` | 520 B | 316 B | +204 B | `experiments/semantic_equivalence/h8_ui_status_affinity_candidate.cpp` |
| `0x002D931C` | 764 B | 440 B | +324 B | `experiments/semantic_equivalence/h8_ui_statusdown_init_candidate.cpp` |
| `0x001EE7C8` | 384 B | 324 B | +60 B | `experiments/semantic_equivalence/h8_ui_statusdown_itemlist_candidate.cpp` |
| `0x0032C4BC` | 372 B | 208 B | +164 B | `experiments/semantic_equivalence/h8_ui_statusdown_itemsort_candidate.cpp` |
| `0x001EE5A4` | 548 B | 368 B | +180 B | `experiments/semantic_equivalence/h8_ui_statusdown_skilllist_candidate.cpp` |
| **Total** | **4,080 B** | **2,472 B** | **+1,608 B** | 8 subsistemas de Camp, Status e Inventario |

## Artefactos y Huellas Criptográficas

- **Imagen binaria final compuesta:** `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.bin`
  - SHA-256: `bddb53a22a86d9759eb138164ddbc6652f00e5066446c2ef6c85c3a6bb8e3b6d`
- **Parche LayeredFS IPS:** `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.ips`
  - SHA-256: `dc766de6633d771d9ce206d324a864ce61e26722e4d2d4715c1be3587b08f091` (21,362 bytes)
  - Verificación Round-trip IPS: PASSED
- **Partida de prueba fija:** `sdds4game1.sav`
  - SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`

## Pruebas de aceptación superadas

1. **Compilación Clang ARMv6K:** Todos los candidatos compilan en C++ reproducible sin desbordar el tamaño de la ventana binaria original (+1,608 B de margen libre total).
2. **Pruebas Diferenciales Unicorn:** Simulación ARM bit a bit verificando registros de retorno, efectos de memoria, argumentos a funciones auxiliares y sensibilidad ante mutaciones (100% aprobado en los 8 componentes).
3. **Staging Compuesto:** Mod IPS generado y verificado contra `code.h7-final.bin` con ida y vuelta exacta.
4. **Verificación Autónoma en Azahar:** Paridad idéntica en arranque, título, carga de partida y 250 callbacks de exploración de campo sin regresiones.
