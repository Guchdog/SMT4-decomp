# Auditoría runtime H2: APT Utility-4 tailstep

Revisión independiente del packet runtime. El JSON registra un hit T05 único en `0x002C5638` (hilo 1, LR `0x00103E84`, SP `0x0FFFFF00`) y un paso `s` del mismo hilo hasta `0x002C0EFC`, conservando LR/SP. El `code.bin` original confirma el branch ARM incondicional. LR es compatible con el retorno del BL de `0x00103E80`, pero no prueba historial completo del caller ni explica las 6,452 líneas HLE Utility-4 reportadas para Run-028.

El listener aparece ligado a `127.0.0.1:61582`/PID 22304; el JSON registra `z0` confirmado antes del paso, hijo terminado, puerto liberado y staging eliminado. El log preservado se trunca después del ACK de `p8`; la limpieza final se respalda en el JSON, no en el log. El JSON afirma que CCI, seed manifest, fixture y save de staging permanecieron iguales; `inputs.save_fixture_staged=false` contradice la existencia del `stage.staged_save_path` con hashes before/after. La attestation offline es `passed_with_warnings`, con cuatro avisos de identidad de fuente en el gate diferencial H2.

Alcance: no inicié Azahar/GDB ni pruebas. En el primer pase de auditoría recalculé hash de las 110 rutas del packet de captura, que pueden incluir entradas desechables de save/perfil; fue una lectura de hashes sin modificaciones. Se informó al coordinador y el auditor se corrigió para no abrirlas. No abrí deliberadamente el save fuente; esa no-accesión solo está afirmada por la captura, no verificada independientemente.

Recomendación: conservar como evidencia de una única ruta dinámica; no repetir arranque solo para confirmar el destino. No cuenta como cierre de H2 ni como equivalencia.

Detalle y hashes: `checks/runtime-review.md`; verificación reproducible: `checks/audit_runtime_capture.py` y `checks/evidence-audit.json`.
