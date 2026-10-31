# H9 — Catedral de las Sombras: Fusión y Compendio (Cathedral of Shadows: Fusion & Compendium)

Estado: cerrado (2026-10-30)
Responsable de integración: Altair (Coordinator)
Revisión base y fecha: codex/semantic-equivalence-experiment, 2026-10-30

## Resultado alcanzado

Catedral de las Sombras (Jakyou / Mido), subsistema de fusión de demonios, gestión del Compendio (Devil Book), habilidades de Legión e interfaz de ordenación en Shin Megami Tensei IV reconstruidos en C++ legible y verificable:
1. Inicialización de efectos y partículas 3D de fusión (`UniteEffect_Init`, `0x002E315C`): 244 B / 344 B ventana (+100 B margen).
2. Inicialización del gestor del Compendio de Demonios (`bibleMain_Init`, `0x00269CC8`): 228 B / 352 B ventana (+124 B margen).
3. Configuración de habilidades de Legión y tareas (`bibleLegionSkill_Init`, `0x003AB770`): 404 B / 592 B ventana (+188 B margen).
4. Gestor de dibujado estereoscópico superior/inferior de Legión (`bibleLegionDraw_Init`, `0x003AD300`): 484 B / 596 B ventana (+112 B margen).
5. Modal de ordenación de fusión y compendio (`SortMenu_Init`, `0x0029E63C`): 364 B / 644 B ventana (+280 B margen).
6. Evaluación de catálogo de fusión, agrupación por raza y qsort (`UniteCtrl_RosterPopulate`, `0x003C9EBC`): 504 B / 664 B ventana (+160 B margen).
7. Inspector y visualizador de demonios del compendio (`bibleDevil_Init`, `0x003A7AD8`): 504 B / 668 B ventana (+164 B margen).
8. Asistente y HUD dinámico de botones de ayuda (`ButtonHelp_Init`, `0x0028D974`): 604 B / 736 B ventana (+132 B margen).

El escenario compara la ejecución bit a bit de estados, estructuras de datos, offsets y efectos de memoria entre el código original y el reemplazo integrado reconstruido en C++, validado de forma autónoma en el emulador Azahar con 0 regresiones.

## Candidatos reconstruidos e integrados

| Función / VMA | Ventana Orig | Candidato C++ | Margen NOP | Archivo Fuente |
|---|---|---|---|---|
| `0x002E315C` | 344 B | 244 B | +100 B | `experiments/semantic_equivalence/h9_camp_uniteeffect_init_candidate.cpp` |
| `0x00269CC8` | 352 B | 228 B | +124 B | `experiments/semantic_equivalence/h9_camp_biblemain_init_candidate.cpp` |
| `0x003AB770` | 592 B | 404 B | +188 B | `experiments/semantic_equivalence/h9_camp_biblelegionskill_init_candidate.cpp` |
| `0x003AD300` | 596 B | 484 B | +112 B | `experiments/semantic_equivalence/h9_camp_biblelegiondraw_init_candidate.cpp` |
| `0x0029E63C` | 644 B | 364 B | +280 B | `experiments/semantic_equivalence/h9_camp_sortmenu_init_candidate.cpp` |
| `0x003C9EBC` | 664 B | 504 B | +160 B | `experiments/semantic_equivalence/h9_camp_unitectrl_roster_candidate.cpp` |
| `0x003A7AD8` | 668 B | 504 B | +164 B | `experiments/semantic_equivalence/h9_camp_bibledevil_init_candidate.cpp` |
| `0x0028D974` | 736 B | 604 B | +132 B | `experiments/semantic_equivalence/h9_camp_buttonhelp_init_candidate.cpp` |
| **Total** | **4,596 B** | **3,328 B** | **+1,268 B** | 8 subsistemas de Fusión y Compendio |

## Artefactos y Huellas Criptográficas

- **Imagen binaria final compuesta:** `build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.bin`
  - SHA-256: `0043ccce8b7bf4a53bbe5312414b27d8c0184345cf674a7e11c1759d0af667ac`
- **Parche LayeredFS IPS:** `build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.ips`
  - SHA-256: `975fcde2a8cbdd4b332126974af00ce2d7588517ed30bc2130c160f8968fdd20` (27,208 bytes)
  - Verificación Round-trip IPS: PASSED
- **Partida de prueba fija:** `sdds4game1.sav`
  - SHA-256: `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`

## Pruebas de aceptación superadas

1. **Compilación Clang ARMv6K:** Todos los candidatos compilan en C++ reproducible sin desbordar el tamaño de la ventana binaria original (+1,268 B de margen libre total).
2. **Pruebas Diferenciales Unicorn:** Simulación ARM bit a bit verificando registros de retorno, efectos de memoria, argumentos a funciones auxiliares y sensibilidad ante mutaciones (100% aprobado en los 8 componentes).
3. **Staging Compuesto:** Mod IPS generado y verificado contra `code.h8-final.bin` con ida y vuelta exacta.
4. **Verificación Autónoma en Azahar:** Paridad idéntica en arranque, título, carga de partida y 250 callbacks de exploración de campo sin regresiones.
