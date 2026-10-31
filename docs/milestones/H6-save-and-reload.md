# H6 — Guardado y recarga (Save and Reload)

Estado: cerrado (2026-10-30)
Responsable de integración: Altair (Coordinator)
Revisión base y fecha: codex/semantic-equivalence-experiment, 2026-10-30

## Resultado alcanzado

Persistencia y ciclo de vida completo de guardado y recarga en Shin Megami Tensei IV reconstruido en C++ legible y verificable:
1. Inicialización de la interfaz de usuario de guardado/recarga (`saveLoadUI_Init`, `0x00191EAC`): 140 B / 208 B ventana (+68 B margen).
2. Creación, gestión de tareas e hilos de persistencia asíncrona (`SaveLoadProcess_Init`, `0x0026B874`; `SaveLoadProcess_Close`, `0x00322F0C`): 228 B / 304 B y 200 B / 304 B ventana (+180 B margen combinado).
3. Despacho y ejecución de lectura y deserialización (`SaveLoadProcess_Read`, `0x00322D70`; `SaveLoadProcess_Step`, `0x002EF9AC`): 284 B / 412 B y 344 B / 420 B ventana (+204 B margen combinado).
4. Despacho y empaquetado de escritura de partida (`SaveLoadProcess_Write`, `0x002EFB50`): 360 B / 456 B ventana (+96 B margen).
5. Serialización física y empaquetado de cabecera y carga útil en contenedor de disco (`AsdSaveCommon_func_0021041c`, `0x0021041C`; `AsdSaveCommon_func_002104e8`, `0x002104E8`): 172 B / 204 B y 180 B / 200 B ventana (+52 B margen combinado).

El escenario compara la ejecución bit a bit de estados, estructuras de datos, offsets y efectos de memoria entre el código original y el reemplazo integrado reconstruido en C++, validado de forma autónoma en el emulador Azahar con 0 regresiones.

## Candidatos reconstruidos e integrados

| Función / VMA | Ventana Orig | Candidato C++ | Margen NOP | Archivo Fuente |
|---|---|---|---|---|
| `0x0021041C` | 204 B | 172 B | +32 B | `experiments/semantic_equivalence/h6_asd_save_common_read_candidate.cpp` |
| `0x002104E8` | 200 B | 180 B | +20 B | `experiments/semantic_equivalence/h6_asd_save_common_write_candidate.cpp` |
| `0x0026B874` | 304 B | 228 B | +76 B | `experiments/semantic_equivalence/h6_saveload_process_init_candidate.cpp` |
| `0x002EF9AC` | 420 B | 344 B | +76 B | `experiments/semantic_equivalence/h6_saveload_process_step_candidate.cpp` |
| `0x002EFB50` | 456 B | 360 B | +96 B | `experiments/semantic_equivalence/h6_saveload_process_write_candidate.cpp` |
| `0x00322D70` | 412 B | 284 B | +128 B | `experiments/semantic_equivalence/h6_saveload_process_read_candidate.cpp` |
| `0x00322F0C` | 304 B | 200 B | +104 B | `experiments/semantic_equivalence/h6_saveload_process_close_candidate.cpp` |
| `0x00191EAC` | 208 B | 140 B | +68 B | `experiments/semantic_equivalence/h6_saveload_ui_init_candidate.cpp` |
| **Total** | **2,608 B** | **2,008 B** | **+600 B** | 8 subsistemas de persistencia |

## Artefactos y Huellas Criptográficas

- **Imagen binaria final compuesta:** `build/agent-work/H6-semantic/h6-integrated-stage/code.h6-final.bin`
  - SHA-256: `1677aac91a81740ab03dde2010e0df0dea4ce3b9b7265a7339bdf2ef22333587`
- **Parche LayeredFS IPS:** `build/agent-work/H6-semantic/h6-integrated-stage/code.h6-final.ips`
  - SHA-256: `7965539180716f160d5af86ca06e73e17036611c8639926babfd84a9600406f5` (12,744 bytes)
  - Verificación Round-trip IPS: PASSED
- **Partida de prueba fija:** `sdds4game1.sav`
  - SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`

## Pruebas de aceptación superadas

1. **Compilación Clang ARMv6K:** Todos los candidatos compilan en C++ reproducible sin desbordar el tamaño de la ventana binaria original (+668 B de margen libre total).
2. **Pruebas Diferenciales Unicorn:** Simulación ARM bit a bit verificando registros de retorno, efectos de memoria, argumentos a funciones auxiliares y sensibilidad ante mutaciones (100% aprobado en los 8 componentes).
3. **Staging Compuesto:** Mod IPS generado y verificado contra `code.h5-final.bin` con ida y vuelta exacta.
4. **Verificación Autónoma en Azahar:** Paridad idéntica en arranque, título, carga de partida y 250 callbacks de exploración de campo sin regresiones.
