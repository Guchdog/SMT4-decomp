# H10 — Burroughs, Misiones (Quests) y Apps (Burroughs, Quests, and Apps)

Estado: cerrado (2026-10-30)
Responsable de integración: Altair (Coordinator)
Revisión base y fecha: codex/semantic-equivalence-experiment, 2026-10-30

## Resultado alcanzado

Burroughs, sistema de Misiones (Quests principales y Challenge Quests), Apps de Burroughs y Demonica App Store en Shin Megami Tensei IV reconstruidos en C++ legible y verificable:
1. Resolución de puntero de guardado de Burroughs y Quests (`Burroughs_GetSaveData`, `0x002A0FAC`): 24 B / 24 B ventana (+0 B margen).
2. Despachador de aplicaciones de Burroughs y audio (`Burroughs_AppDispatch`, `0x002A0EA8`): 160 B / 168 B ventana (+8 B margen).
3. Reseteo de selección y categoría de Quests (`Quest_ResetSelection`, `0x0026A004`): 36 B / 40 B ventana (+4 B margen).
4. Evaluación de condiciones objetivo de Quests (`Quest_EvaluateTargetCondition`, `0x0026A86C`): 128 B / 152 B ventana (+24 B margen).
5. Comprobación de disponibilidad de Quests (`Quest_GetAvailability`, `0x0026A9FC`): 156 B / 196 B ventana (+40 B margen).
6. Desempaquetado de definición estática a UI dinámica (`Quest_UnpackEntryData`, `0x0026AAC0`): 240 B / 256 B ventana (+16 B margen).
7. Registro de compra y flag de estado de App Store (`AppStore_SetFlag`, `0x003253D8`): 56 B / 56 B ventana (+0 B margen).
8. Consulta de parámetros y formato de texto de App Store (`AppStore_GetAppParam`, `0x00325444`): 52 B / 52 B ventana (+0 B margen).

El escenario compara la ejecución bit a bit de estados, estructuras de datos, offsets y efectos de memoria entre el código original y el reemplazo integrado reconstruido en C++, validado de forma autónoma en el emulador Azahar con 0 regresiones.

## Candidatos reconstruidos e integrados

| Función / VMA | Ventana Orig | Candidato C++ | Margen NOP | Archivo Fuente |
|---|---|---|---|---|
| `0x002A0FAC` | 24 B | 24 B | +0 B | `experiments/semantic_equivalence/h10_camp_burroughs_getsavedata_candidate.cpp` |
| `0x002A0EA8` | 168 B | 160 B | +8 B | `experiments/semantic_equivalence/h10_camp_burroughs_appdispatch_candidate.cpp` |
| `0x0026A004` | 40 B | 36 B | +4 B | `experiments/semantic_equivalence/h10_camp_quest_resetselection_candidate.cpp` |
| `0x0026A86C` | 152 B | 128 B | +24 B | `experiments/semantic_equivalence/h10_camp_quest_evaltarget_candidate.cpp` |
| `0x0026A9FC` | 196 B | 156 B | +40 B | `experiments/semantic_equivalence/h10_camp_quest_getavailability_candidate.cpp` |
| `0x0026AAC0` | 256 B | 240 B | +16 B | `experiments/semantic_equivalence/h10_camp_quest_unpackentry_candidate.cpp` |
| `0x003253D8` | 56 B | 56 B | +0 B | `experiments/semantic_equivalence/h10_camp_appstore_setflag_candidate.cpp` |
| `0x00325444` | 52 B | 52 B | +0 B | `experiments/semantic_equivalence/h10_camp_appstore_getappparam_candidate.cpp` |
| **Total** | **944 B** | **852 B** | **+92 B** | 8 subsistemas de Burroughs, Quests y Apps |

## Artefactos y Huellas Criptográficas

- **Imagen binaria final compuesta:** `build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.bin`
  - SHA-256: `8233530ba0df84acc66bf6196153403d257e8bbfa1aca1537fafcabc51bdc4e3`
- **Parche LayeredFS IPS:** `build/agent-work/H10-semantic/h10-integrated-stage/code.h10-final.ips`
  - SHA-256: `db659411fb8e4c9c17f7246a8ae3b488cb42191d1648a18fdcdeaca9ad2c0122` (28,496 bytes)
  - Verificación Round-trip IPS: PASSED
- **Partida de prueba fija:** `sdds4game1.sav`
  - SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`

## Pruebas de aceptación superadas

1. **Compilación Clang ARMv6K:** Todos los candidatos compilan en C++ reproducible sin desbordar el tamaño de la ventana binaria original (+92 B de margen libre total).
2. **Pruebas Diferenciales Unicorn:** Simulación ARM bit a bit verificando registros de retorno, efectos de memoria, argumentos a funciones auxiliares y sensibilidad ante mutaciones (100% aprobado en los 8 componentes).
3. **Staging Compuesto:** Mod IPS generado y verificado contra `code.h9-final.bin` con ida y vuelta exacta.
4. **Verificación Autónoma en Azahar:** Paridad idéntica en arranque, título, carga de partida y 250 callbacks de exploración de campo sin regresiones.
