# Revisión correctiva de cierre RSP

La corrección es adecuada en el alcance revisado: `execute.finally` pone `process_stopped=false` antes del retry, y `confirmed_stopped` solo es verdadero tras `poll() is not None`. Si la terminación persiste o `poll()` falla, los 62 tests confirman socket abierto, no `D`, estado no confirmado y `stage_cleanup.removed=false`. La prueba de stop/retry exitoso confirma orden de cierre y hashes sintéticos.

La ruta que conserva el stage no afirma directamente `Path(stage).exists()`, aunque el branch del código salta `remove_owned_stage`; esto es una mejora menor de aserción, no un bloqueo. No se usaron runtime, perfil ni save real. Informe detallado: `checks/runtime-review.md`.
