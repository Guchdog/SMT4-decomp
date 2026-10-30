# Independent review: readiness differential harness correction

## Review result

**Disposition:** accept the corrected fixture layout and expanded ABI preservation checks for the isolated `TitleConfig_IsReady` differential. I found no defect in these two corrections. This does not approve caller composition, production promotion, or H2 runtime equivalence.

## Fixture bounds

The runner maps `code.bin` at `0x00100000` for `0x00378000` bytes, giving a half-open mapped interval `[0x00100000, 0x00478000)`. The configured pinned image is `0x00377000` bytes, so the map includes the whole `code.bin` plus one page. The synthetic workspace maps at `0x00500000` for `0x1000` bytes, interval `[0x00500000, 0x00501000)`, which is disjoint from the full map. The overlap predicate uses the standard half-open interval test; the test case at `0x00410000` is rejected as expected. The non-null cases map the workspace as its own Unicorn region before writing the task pointer.

The pinned image hash/size guard remains in force. For future image layouts, keeping `CODE_MAP_SIZE` tied to a checked bound (at least `len(image)`) would avoid relying on a manually maintained slack constant. With the currently pinned `0x00377000` image and `0x00378000` map, no overlap or unmapped-image issue is present.

## ABI preservation checks

Before each callback, the runner seeds `r4-r11` with distinct 32-bit values and `d8-d15` with distinct 64-bit values, and records the initial SP. After the return sentinel, it checks every seeded register plus SP. `compare()` rejects either execution if any preservation entry is false, before it compares return value, PC, and helper trace. This covers ARM callee-saved core registers and hard-float callee-saved VFP registers for this build target. Both original and candidate receive the same initialization.

The focused test suite includes an accepted complete preservation dictionary and a corruption rejection case; the latter currently mutates SP, while inspection confirms the same `all(preserved.values())` gate covers every GPR/VFP key. The stored corrected differential reports 4/4 lifecycle cases passing and detects the always-ready negative control. The corresponding task handoff records seven focused tests passing and the differential rerun.

## Remaining limits

The registration lookup at `0x002BF41C` remains mocked identically in both executions. The title state-10 caller is statically traced, not composed with the candidate. No scheduler lifecycle, Azahar, input, persistence, or restart scenario has been verified. The candidate and ledger remain unchanged and experimental.

No blocking issue was found in the corrected fixture or ABI checks. The only suggested hardening is to assert that the configured Unicorn image map covers the pinned image size, so future configuration drift cannot silently invalidate the current bound calculation.
