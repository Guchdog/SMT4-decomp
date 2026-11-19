# H2 titleConfig: auditoría de estado vigente

## Dictamen

El estado más reciente que debe gobernar H2 es el cierre fechado 2026-11-16 en `docs/milestones/H2-audio-settings.md`, apoyado por el ciclo de vida emparejado run-001. Los párrafos anteriores de la misma ficha que dicen «validación parcial», readiness detenida o reentrada no observada describen runs anteriores (principalmente 2026-11-02 y 2026-11-09); no describen el run-001 más reciente y deben leerse como historial. `config/reconstruction.json` ya selecciona H18, coherente con que H2 dejó de ser el hito activo.

La evidencia vigente soporta equivalencia del escenario H2 **controlado y definido**: imagen acumulada fija, 51 acciones iguales, 20/20 checkpoints, cierre/reentrada y observaciones tras reinicio emparejadas. No demuestra entrada física ni una ruta natural de cierre de ComWin: el runner inyecta consultas lógicas y fuerza la respuesta de confirmación del diálogo por `0x002C1830(0,1) -> 1`. La declaración de cierre es razonable para el recorrido integrado y la lógica reconstruida dentro del alcance documentado, con esas dependencias originales/controladas explicitadas; no equivale a equivalencia total del juego.

Precisión sobre «persistencia»: el reporte no dice que el cambio confirmado 7/7/7 sobreviva al reinicio. De hecho, `restart_matches_confirmation_original` y `restart_matches_confirmation_patched` son `false`, y ambos vuelven a 8/8/8 (`g_ConfigBytes=3250503000000000`). Lo que sí coincide es el resultado del reinicio entre original y parcheado (`restart_persistence_outcome_matched=true`). Para evitar una lectura engañosa, el resumen de `docs/functional-status.md` debería describirlo como **paridad del resultado tras reinicio (ambos restauran 8/8/8)**, no como persistencia de los valores confirmados. No edité ese archivo.

## Proveniencia y hashes comprobados

| Artefacto | SHA-256 verificado |
|---|---|
| Original `extracted/exefs/code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Imagen acumulada `.../staged-image/code.h2-cumulative.bin` | `d0d6c4f110143c4d9a4da0d03072dfcf20b58e41c99542435fe52c9c0f97a04b` |
| IPS acumulado `.../staged-image/code.h2-cumulative.ips` | `09cdd0dc4d0dc9a19c78be1e6882e20bf5bd20eaba13da2fdafeaa47f9cd89b3` |
| Manifiesto de composición del runtime | `db8e52d933bc50c28b17cacb4d0e9613e03ceeac6f2cba3fc1f383bce3778c95` |
| Reporte de gates offline | `65b00e9b50eae4750b919fafdbadb59c6451187211660a22553f614b6e67c414` |
| Reporte de caller composition | `cefd563551ffda29371d8d0e25e9c6b1b498780bec2cf3775a780617b2b673d7` |
| Runner de ciclo de vida | `676ee26cc8bc9a3d6da8bfe31885d13bce41aef4aa2bf206b050ecc538041545` |
| Reporte runtime `autonomous-gdb-verification.json` | `bb5343fa77fc67967c47b022ad1c321f88b25bf0af110a6ffd5003d215b3cf8b` |

El manifiesto confirma original pinneado, 998 registros IPS, `ips_roundtrip=true`, `zero_slot_overlap=true` y siete slots sobrepuestos con ramas ARM pares. El reporte runtime pinnea el mismo original, la imagen/IPS anteriores, Azahar privado `1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682` y CCI `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`. Ambos perfiles registran el mismo SHA del ejecutable stageado. Estos son hashes del paquete de runtime, no una recompilación hecha por este audit.

Hay un audit previo de run-005 que reporta metadatos de staging ambiguos y cero eventos `logical_query_return`; es correcto para ese run manual viejo, no para run-001. El run-001 posterior incluye el ejecutable staged hash en ambos perfiles, 51 acciones por lado, 20 checkpoints, capturas de reentrada y cierre. No mezclar esos paquetes. Un `function-body-comparison.json` previo concilió bodies de cuatro símbolos contra otra imagen H2 y encontró discrepancias de hash en TUs completos; por tanto ese resultado no debe presentarse como una recompilación fresca de cada fuente que forma la imagen `d0d6c4f1`. La composición y el runtime sí pinnean la imagen final; la identidad de cuerpos tiene su evidencia propia y alcance separado.

## Evidencia offline vigente

`offline-gates-report.json` registra `all_offline_gates_passed=true`: `0x00286928_q0` (296 directos, 4 callback, 3 pointer timing), callbacks H2 (Draw 46/46, Calc 16/16, ReadyGate 4/4), caller composition H2 3/3 y `0x00207D84` in-slot con todos los diferenciales/caller/controles, IPS replay y cero colisiones. El informe de cierre agrega los gates históricos complementarios de inicializador, Secondary y caller-cumulative. Son evidencias offline basadas en casos/RAM controlados y sus límites deben conservarse; no reemplazan la comparación runtime.

## Evidencia runtime vigente y límites

El reporte del 2026-11-16 tiene `passed=true`, `scripted_input_traces_equal=true`, 51 acciones, 20 checkpoints coincidentes y `controlled_lifecycle_completed=true`. Ambos perfiles completan readiness; la secuencia State 2 → State 3 → State 4 → `Title_ResetForBoot` termina en 72 frames. Hay cancelación sin cambio, edición de BGM/SE/Voice con extremos/default reset, confirmación, reentrada same-session y reinicio de proceso. Tras confirmación, same-session reentry da 7/7/7; tras reinicio ambos vuelven a 8/8/8. Los exits de `WM_CLOSE` son limpios (`0`). Perfil/soporte y ejecutable privado se marcan sin cambios.

Las entradas son respuestas lógicas controladas, no un mapeo de botones físicos. Para desbloquear la ruta de readiness se controla la respuesta del servicio `0x002C1830` del diálogo ComWin; no se reconstruye ni valida el mecanismo natural que cerraría ese diálogo. Las funciones fuera de los siete slots integrados quedan originales. El estado «Cerrado» no avala esos servicios originales ni todos los estados posibles del título.

## Próxima tarea integrada concreta

No reabrir la implementación H2 ni repetir run-005. Si se requiere ampliar el alcance, asignar una única revisión integrada de la ruta de confirmación ComWin: rastrear qué evento/estado natural debe hacer que `0x002C1830` retorne éxito, sustituir ese hook únicamente en el escenario desechable por la ruta real, y volver a ejecutar la misma comparación original/parcheado con las mismas acciones, 20 checkpoints y guardas de perfil. Mantener las pruebas offline antes del runtime. Si la prioridad pasa a otro milestone, registrar H2 como cerrado con la nota semántica de reinicio indicada arriba y enfocar el trabajo en el milestone activo H18.

## Procedimiento de este audit

Solo lectura: `Get-Content` de las fichas/runtime docs; Python `hashlib` para los artefactos listados y `json` para inspeccionar flags, acciones, checkpoints, manifiesto y gates; `git status --short` para reconocer cambios compartidos, sin tocarlos. No ejecuté build, pruebas, emulador ni debugger. La imagen original, los informes, el runner y los inputs permanecieron congelados durante esta inspección.
