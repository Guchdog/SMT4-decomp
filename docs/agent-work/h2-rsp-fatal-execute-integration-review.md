# Revisión de integración RSP fatal (H2)

La prueba sintética llama al `execute` y `capture_session` reales con `DeadlineRsp` sustituido por un fake. Simula respuesta perdida al insertar `Z0`; confirma que el callback real de `execute` termina el proceso falso antes del cierre de socket falso, omite `D` y elimina el staging temporal. El test pasó: `python -B -m unittest tests.test_h2_rsp_fatal_execute_integration -v` (1/1, exit 0).

El alcance queda limitado al error de `Z0` mayúscula. No valida framing/deadlines/socket o proceso real; no simula si el target aplicó el breakpoint pese a respuesta perdida. `z0`, `s` y `D` no están cubiertos en integración execute-level; `z0` y `s` tienen cobertura más baja en `capture_session`. Si falla el callback fatal, `execute.finally` vuelve a intentar detener al hijo, pero no cierra explícitamente el socket; la posible fuga en un segundo intento exitoso tampoco está cubierta. El test no verifica explícitamente `z0` ausente ni hashes before/after de todos los artefactos sintéticos. No se usaron perfiles ni saves reales o desechables.

Ver informe detallado y límites en `checks/runtime-review.md`; packet inputs 14/14 en `checks/input-hash-audit.json`.
