# Independent review: H2 Draw cache split probe

## Review result

The frozen probe is internally consistent as a **size and relocation feasibility result**. I found no helper-order, branch signedness, literal-content, or size-arithmetic defect that would block proceeding to a placement-aware builder. The proposed Draw main and cache helper/string fit their assigned ranges on the reported object sizes.

This does not validate the current production Draw implementation semantically. The extraction is from a focused production-TU compile, but no differential was run against the extracted production symbol at its final VMA; no combined Calc+Draw image, caller composition, or runtime comparison exists. The existing 46-case Draw evidence is for the isolated candidate under controlled helper mocks, not this production split.

## Source and behavior review

The `git diff` for `src/engine/leaf_batch43_a.cpp` replaces the prior naked assembly for `ui_func_002cafd0` with the readable wrapper and adds its local Draw helpers/constants; it does not show unrelated function edits in that file. The added `title_config_draw_cached_render_update` helper preserves the inspected order: call render-value helper `0x002C5FA4` with `(6, first, second)`, read the selected cache slot, write its new value, conditionally call the indirect callback with that value when dirty or changed, then clear the dirty byte. All seven source sites remain in their former surrounding panel/touch order, with arguments `(1,0)` and `(7,0)` as appropriate.

The `static_cast<draw_u32>(absolute_index) < 3u` condition preserves the reviewed unsigned `CMP`/`BHS` behavior, including skipping table access for negative indices. The Draw callback keeps the observed normal return `r0=0` by returning `u32{0}`. The shared `TitleConfig_Draw(void*)` declaration is still `void`; the production source uses the ledger-named `ui_func_002cafd0` symbol and does not change the shared declaration. Before promotion, the actual registration/callback type and whether the return value is consumed should be reconciled against the task factory/caller.

The production compile record uses the hard-float ARM target and the wrapper passes the reviewed floating-point arguments to the font helper in the reported order. The probe does not itself prove final-address VFP/stack ABI preservation; the final production-symbol differential must compare those effects. The local format string remains exactly `%s\0` (`25 73 00`). The original literal at `0x002CB410` is within the 1,464-byte replacement body, so moving it is necessary; the recorded `R_ARM_ABS32` relocation is the one reference that the builder must retarget.

## Object, relocations, and placement arithmetic

I checked the extraction JSON against the production object hash and confirmed the seven `R_ARM_CALL` entries all target `_ZL38title_config_draw_cached_render_updatejj`, at main-symbol offsets 332, 400, 440, 480, 524, 804, and 840. The eighth relocation is `R_ARM_ABS32` at offset 1,460; it resolves to local `.rodata` with section addend 0 and symbol `_ZL15kDrawTextFormat`. The helper has no relocations. These are the full relocation list in the frozen extraction; the actual builder still needs to apply each ARM REL relocation correctly and reject any unexpected relocation.

The main symbol is 1,464 bytes against the original `[0x002CAFD0,0x002CB75C)` span of 1,932 bytes, leaving 468 bytes. The Calc cave tail is `[0x003FEE54,0x003FF000)`, exactly 428 bytes. Starting the 4-byte-aligned 124-byte helper at `0x003FEE54` ends it at `0x003FEED0`; placing the 3-byte string there gives 127 bytes total, rounded to 128, leaving 300 bytes. The proposed helper is about 1.27 MiB from the Draw call sites, within ARM `BL` range. The arithmetic is sound, but the combined image must verify the resolved call instructions/targets and exact address map rather than relying only on the object report.

## Recommendation and limits

Proceed to a placement-aware builder as a bounded engineering step: reserve the helper and `%s\0` in the verified tail, replace only the 1,464-byte main body in the original span, resolve all seven helper calls and the local absolute string reference, and emit a manifest that checks capacity, alignment, overlap, branch range, ARM state, and bytes outside authorized patch records. Preserve the existing Calc placement and validate both callbacks against the same merged image.

Do not treat the probe as semantic acceptance or promotion evidence. Required follow-up includes the Draw differential using the production-extracted symbol at final VMA, the retained wrong-stride negative control, ABI/trace/memory comparisons, a bounded initialized caller/task composition, and a Calc sequence regression on the merged image. The callback declaration/caller's treatment of `r0` remains an integration question. No emulator/runtime or visible UI behavior is established. This review performed no compilation, patching, ledger/source edits, emulator, RSP, profile, keyboard, or mouse operation.

## Provenance

- Frozen review packet: `build/agent-work/H2-semantic/h2-draw-cache-split-probe-review/run-001/task.json`; all declared input SHA-256 values matched before and after review.
- Production source SHA-256: `e5c6414cd37d2d6fc9928ca85eb5466a8c07bcec224a887616cb383ac408d64c`.
- Production object SHA-256: `0513196e3d93398036feba0177fc92cadadba87589068dc0605da64b0658ede2`.
- Extraction report SHA-256: `e0cf69d3ce6fb3c1a6cad4e8eef15b2bb1fbf7597cf5bb074a4f1d6b9856f246`.
- Pinned `code.bin` SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
