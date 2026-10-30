# H2 final image rebuild after Draw formatter Thumb correction

## Result

Rebuilt the full production-derived H2 image from the pinned original with the reviewed Draw formatter pointer. The fresh patcher output keeps the exact previous production placements and changes one byte in the final image: offset `0x1CB258` (`0x80` to `0x81`), the immediate that forms the Thumb-tagged formatter pointer before `BLX r3`.

The current Secondary translation unit had changed outside the selected function since the earlier H2 build. A fresh private production object was compiled; `engine_func_002caef0` is byte-identical to the previously reviewed 292-byte, relocation-free body. The patcher's source/object pins now identify that current object. The final ready-gate input is the reviewed direct-call-optimization object identified by the prior final manifest.

## Reproducible artifacts

- Pinned original `code.bin`: SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Final image: `build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final/code.combined.bin`, SHA-256 `cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4`.
- IPS: `build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final/code.combined.ips`, SHA-256 `08dc412ae2045858cc5e087ca97527edd32622311c2bd0b9a219276fec7ba758`.
- Manifest: `build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/combined-build-final/manifest.json`, SHA-256 `4002ab29da801d36eafd17fd728d0473f50d7d10ec6c786ba3135b6b431140cf`.
- The prior final image differed from this image by exactly one byte at `0x1CB258`. The builder reports 4,006 changed bytes from original and confirms the IPS reproduces the patched image while confining writes to declared records.
- Draw remains 1,464 bytes in its original 1,932-byte span; it returns at `0x002CB55C`, before the retained suffix. The Draw helper remains 124 bytes at `0x003FEE54`; `%s\0` is at `0x003FEED0`.
- The shared text cave `[0x003FE624,0x003FF000)` is 2,524 bytes; 2,516 are used and 8 remain. Calc, Draw helper/string, and Secondary placements and all resolved relocation records are recorded in the manifest.

## Differential and caller evidence

`tools/h2_combined_offline_validation.py` passed against the new final addresses:

- Draw: 46/46 cases; target-plus-four helper negative control detected.
- Calc: 16/16 persistent sequences, 54/54 ticks for seeds 7 and 20261024; wrong-map control detected.
- Secondary: 34/34 cases; its existing negative control detected.
- Initializer: 10/10 cases; wrong sprite-group-count control detected.
- Ready gate: 4/4 cases; always-ready control detected.

Report: `build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/offline-final-validation/report.json`, SHA-256 `b8d8394293cfad846e75cf9fccf2ec536ea1a312461cd63d91705c2bf14e5c8c`.

The production initializer caller composition passed 3/3 State 9/10 cases with its wrong-Calc-address control detected. Report: `build/agent-work/H2-semantic/h2-thumb-reintegrate-final-image/run-004/caller-composition/report.json`, SHA-256 `0565bb05a18ddd002ee950208565ca33d5b55bb5c96f43a3074838c7f2a3610a`. As documented by the harness, this is partial caller evidence with explicit HLE boundaries; it does not schedule the real callbacks.

Focused patcher tests passed 4/4. Thumb-state experiment tests passed 5/5. No emulator or automated host input was used for this rebuild.

## Limits and next action

The offline helper boundaries still mock real rendering, formatting, touch, TBB and selected service behavior. The prior full H2 image and Draw/Secondary split crashed at Audio Settings; this corrected image has not yet been launched or manually checked. The build and differential evidence do not establish runtime or save-persistence equivalence. Independently review the new manifest/image/IPS and offline reports, then prepare a fresh isolated Azahar CLI profile with GDB/RPC disabled for the user's manual Audio Settings scenario.
