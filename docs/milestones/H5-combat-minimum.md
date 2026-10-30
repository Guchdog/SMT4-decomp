# H5 — Combate mínimo

Estado: completado y cerrado (2026-10-30)  
Responsable de integración: coordinador  
Revisión base y fecha: `codex/semantic-equivalence-experiment`, 2026-10-30

## Resultado esperado

Desde la base de exploración funcional validada en H4, aislar, reconstruir e integrar los subsistemas esenciales del motor de combate de Shin Megami Tensei IV en C++ semántico y editable: evaluación de unidades de grupo vivas/activas en combate (`btlUnit_CheckPartyActive`), discriminación de unidades demonio (`Btl_IsDemonUnit`), despacho de renderizado de selección de objetivos en pantalla superior (`btlTargetSelect_DrawUp`), cálculo e interpolación de retícula y animación de selección de objetivos (`btlTargetSelect_Calc`), inicialización del espacio de trabajo del modal de ayuda (`btlHelp_Init`), inicialización del espacio de trabajo de negociación y diálogo de combate (`btlTalk_Init`), comprobación del ciclo de vida y liberación segura de subobjetos de combate (`Btl_ReleaseState`), y asignación de parámetros de canal de audio/pantalla (`Btl_SetChannelParameter`). Verificar compuertas offline completas (interworking ARM/Thumb, alineación a 4 bytes, cero desbordes de ventana), pruebas diferenciales con controles de mutación, integración en la imagen compuesta y verificación pareada en emulador Azahar.

## Alcance y exclusiones

- **Alcance funcional:**
  - `0x001D29C8`: `btlUnit_CheckPartyActive` (240 B original / 184 B C++ candidato) — Lógica de recorrido de slots activos (8 slots), slots de reserva (8 slots) y grupo de invitados (8 slots) mediante `Unit_Lookup_002ae3f0` y comprobación del estado `*(unit + 0x23) == 3`.
  - `0x002AE464`: `Btl_IsDemonUnit` (16 B / 16 B) — Discriminador de ID de demonio (> 0x190 / 400).
  - `0x002F4AA4`: `btlTargetSelect_DrawUp` (76 B / 68 B) — Despacho condicional de dibujado para modo 1 y modo 2 de selección de objetivos.
  - `0x002E06BC`: `btlTargetSelect_Calc` (236 B / 224 B) — Actualización de animación de retícula, flags de visibilidad de subobjetos y cálculo flotante de interpolación angular (`+1.0f` clamp 30.0f, `+12.0f` wrap 360.0f).
  - `0x001D2528`: `btlHelp_Init` (232 B / 160 B) — Ciclo de vida y creación de tarea "btlHelp Calc" (tag 2, prioridad `0x0020ee34`) y asignación/limpieza de buffer de ayuda.
  - `0x001D2610`: `btlTalk_Init` (308 B / 256 B) — Ciclo de vida y creación de tarea "btlTalk Calc" (tag 2, prioridad `0x0020f35c`), buffer de 0xCC bytes, inicialización de speaker ID y registro del host.
  - `0x002B8A80`: `Btl_ReleaseState` (92 B / 88 B) — Verificación de estado ocupado/libre de subobjeto y liberación segura de memoria dinámica.
  - `0x0011311C`: `Btl_SetChannelParameter` (52 B / 44 B) — Configuración de flags de canal en `g_CombatChannelContext_004c6290` (modos 0x400, 0x401, 0x402).
- **Exclusiones:**
  - Fórmulas completas de IA enemiga, tablas completas de afinidades elementales y animaciones 3D esqueléticas de demonios de alto poligonaje permanecen vinculadas a los recursos originales.

## Dependencias

- Imagen base compuesta H4: `code.h4-final.bin` (SHA-256: `3e0e4ae440cce5e3644f3f8c19f69806bbfd81fee4e285723bd6979625e37dca`).
- Rutinas de CRT y memoria: `Task_Destroy_002bf41c`, `Task_Create_002c4c00`, `Mem_Alloc_002c4b84`, `Free_002c4360`.
- Lookup de entidades y unidades: `Unit_Lookup_002ae3f0`, `SubParty_Lookup_002b9364`, `TargetSelect_GetWork_002c0ac8`.

## Pruebas de aceptación

1. Cada uno de los 8 candidatos C++ se compila limpiamente con Clang ARMv6K para 3DS con cero relocaciones fuera de símbolos identificados.
2. Cada candidato respeta estrictamente el tamaño de ventana del original (longitud candidata <= longitud original).
3. Cada candidato supera la suite de pruebas diferenciales ARM en Unicorn frente al código binario original extraído en múltiples casos válidos, casos límite y controles de mutación negativa.
4. Paquete IPS generado round-trip verificado sobre la base H4, generando `code.h5-final.bin` y `code.h5-final.ips`.
5. Verificación autónoma pareada en emulador Azahar contra la versión retail original, confirmando cero regresiones en pantalla de título, carga de partida, 250 ticks de escena de campo e integridad de guardado y perfiles.

## Candidatos C++ integrados (8 en total)

| Función / VMA | Tamaño (Cand / Orig) | Rol funcional | Archivo de origen |
|---|---|---|---|
| `0x001D29C8` | 184 B / 240 B | Verificación de unidades activas en grupo/reserva/invitados | `experiments/semantic_equivalence/h5_btl_unit_check_party_active_candidate.cpp` |
| `0x002AE464` | 16 B / 16 B | Clasificador de ID de demonio (> 400) | `experiments/semantic_equivalence/h5_btl_is_demon_unit_candidate.cpp` |
| `0x002F4AA4` | 68 B / 76 B | Despacho de dibujado superior de selección de objetivo | `experiments/semantic_equivalence/h5_btl_target_select_draw_up_candidate.cpp` |
| `0x002E06BC` | 224 B / 236 B | Cálculo de retícula y rotación angular de selección de objetivo | `experiments/semantic_equivalence/h5_btl_target_select_calc_candidate.cpp` |
| `0x001D2528` | 160 B / 232 B | Inicialización de modal de ayuda de combate | `experiments/semantic_equivalence/h5_btl_help_init_candidate.cpp` |
| `0x001D2610` | 256 B / 308 B | Inicialización de modal de negociación y talk de combate | `experiments/semantic_equivalence/h5_btl_talk_init_candidate.cpp` |
| `0x002B8A80` | 88 B / 92 B | Verificación de ciclo de vida y liberación de subobjeto | `experiments/semantic_equivalence/h5_btl_release_state_candidate.cpp` |
| `0x0011311C` | 44 B / 52 B | Asignación de parámetros de canal de combate | `experiments/semantic_equivalence/h5_btl_set_channel_param_candidate.cpp` |

**Total de lógica reconstruida en H5:** 1.040 bytes compilados (de 1.252 bytes de ventana original), con 212 bytes de relleno seguro NOP.

## Compuertas offline

- **Interworking ARM/Thumb:** Bit 0 en cero verificado en todos los puntos de entrada y branch targets.
- **Alineación:** 4 bytes garantizados en todas las instrucciones y literales.
- **Diferencial Unicorn:** 100% de coincidencia en todas las suites (`status=passed`, mutación detectada en todos los casos).
- **Imagen compuesta:**
  - Base de entrada H4: `code.h4-final.bin` (SHA-256: `3e0e4ae440cce5e3644f3f8c19f69806bbfd81fee4e285723bd6979625e37dca`).
  - Imagen final H5: `code.h5-final.bin` (SHA-256: `48b73ed0246547dfe6397d6300b61fcbd885688ee70ef28f9b713db1d741ec5d`).
  - Parche IPS H5: `code.h5-final.ips` (SHA-256: `c4f95c37e93e8387544c18465712a5a1f4f1439bfb0b0dacfe41b9fe58f422a4`, tamaño: 10.154 bytes).

## Verificación runtime autónoma pareada (Azahar GDB stub)

- Ejecución autónoma en entorno loopback aislado con stub GDB privado.
- Comparación pareada entre `original` (puerto 54342) y `patched` con `code.h5-final.ips` (puerto 54343).
- Cero divergencias funcionales a lo largo de 250 callbacks de escena tras la carga del guardado conocido.
- Comprobación de persistencia y no alteración de partida ni perfil.

## Estado final y cierre

- Recorrido integrado validado: **Sí**.
- Lógica del alcance reconstruida: **Sí** (gestión de unidades de combate, clasificador de demonios, retícula de selección de objetivo, modales de ayuda y negociación, limpieza de estado y canales).
- Revisión independiente: aprobada en [`h5-autonomous-combat-verify-review.md`](../agent-work/h5-autonomous-combat-verify-review.md).
- Estado final del hito: **CERRADO (2026-10-30)**.
