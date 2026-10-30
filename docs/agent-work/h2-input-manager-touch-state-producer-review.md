# Independent review: H2 input-manager touch-state producer audit

## Recommendation

**Accept the report's principal producer and corrected record-layout conclusions, with a completeness clarification before using it as the full state-byte write inventory.** The pinned image confirms `IfTouch_Init` allocates/publishes a `0x680` manager, registers internal entry `0x00107CCC` as the `TOUCH CALC` task callback, and initializes `manager+0x64E` to signed `-1`, `+0x64A` to 10, and `+0x64C` to zero. The getter reads the live callback fields as stated. `camp_func_002B88C4` writes region data to `manager + 8*index + {0xA,0xC,0xE,0x10}`. The former `manager+0x600+8*index` layout is incorrect.

The report's named write examples are accurate, but they are not a complete list of direct writes to `manager+0x08`. The callback span also contains three conditional clears omitted from its summary: `0x00107F5C`, `0x00107FE8`, and `0x0010800C`; it also sets the byte from `r8` at `0x00107E4C` on the distance branch. This does not overturn the report's opaque-state/unresolved-runtime conclusion, but an exhaustive writer statement should include these sites and conditions.

## Rechecked pinned path

Image: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Function boundaries and names are from `config/functions.csv` at checkout base `1f1179b8cdf22c3e4a5343cb8a528fde64f5aaeb`.

- `IfTouch_Init` (`0x0010299C`) loads the reference count from `0x0043DCB0`; when the manager pointer at `+4` is null, it calls the allocator with size `0x680` and stores the returned pointer at `0x0043DCB4`. The manager pointer is held in `r4`. It calls the size-`0x680` helper, then passes callback pointer `0x00107CCC` on the stack to the task factory with name `TOUCH CALC`; the other stack callback value is `0x0010A28C`. It stores the returned task pointer at `manager+0`, then writes `-1` to `manager+0x64E`, 10 to `manager+0x64A`, and 0 to `manager+0x64C`. The report correctly avoids relying on the clearing helper's undocumented semantics for these explicit values.
- At `0x00107CCC`, the callback loads the manager pointer through `0x0043DCB4`, reads the state byte at `manager+8`, and dispatches by that byte. In its region-hit loops, it passes the four halfwords at `manager+8*i+{0xA,0xC,0xE,0x10}` to `camp_func_002C0144`. A nonzero result at `0x00107D7C` reaches `0x00107D88/0x00107D8C`, which store `r8` to `manager+8` and the loop index `r5` to `manager+0x64E`; in this path `r8` has been set to 1 after the positive manager count check. A nonzero hit at `0x00107EE0` conditionally stores `r8` to `manager+8` and `r5` to `manager+0x64E`; in this callback path `r8` retains its initial value 2. The report's conditional hit-store descriptions are accurate.
- Additional state-byte writes in this same span: `0x00107E4C` stores `r8` after the computed-distance comparison at `0x00107E44` is greater than 8 (the `BLS` to `0x00107E50` is not taken); `0x00107E68` stores 6 only when the `camp_func_002C01B8(0,3)` call at `0x00107E5C` returns nonzero; `0x00107E94` clears the byte only when the helper at `0x00107E8C` returns zero; and `0x00107F04` unconditionally clears it on its dispatch path. Further conditional clears occur at `0x00107F5C` when the signed-halfword difference tested by `CMN` is below the negative bound, at `0x00107FE8` when a negative `manager+0x674` value is incremented to nonnegative, and at `0x0010800C` when a positive value is decremented to nonpositive. The backing helper meanings and runtime schedules remain outside this review.
- `UiTouch_GetRegionTouchState` (`0x0029D8FC`) loads the signed halfword at `manager+0x64E`, compares it to its `s16` argument, and returns the byte at `manager+8` on equality, otherwise zero. This confirms the getter's relation to the fields initialized and updated above, but not a semantic name for the byte's values.

## Registration-record arithmetic

In `camp_func_002B88C4` (`0x002B88C4`), the helper obtains the manager in `r1`. It forms `r2 = manager+0x600` only to load/check the halfword at `r2+0x4A` (absolute `manager+0x64A`) as the insertion index and to increment that metadata afterward. In the insertion blocks, `r1` is reloaded as the manager, and the code computes `r1 = manager + (index << 3)`, then stores halfwords at offsets `0xA`, `0xC`, `0xE`, and `0x10`. The callback's reader loop uses the same manager-plus-index-times-eight base. This directly establishes `manager+8*index+offset`, **not** `manager+0x600+8*index+offset`. The successful return preserves the pre-increment index; capacity failure returns `-1`. The `+0x600` location remains relevant for trailing manager metadata such as `+0x64A/+0x64C/+0x64E`, but it is not added to the record base.

## Required downstream corrections

The newly reviewed manager audit is correct about the producer and the corrected record base, subject to the state-byte inventory clarification above. Earlier dependent documents contain stale statements that should be refreshed by their owners:

- `h2-input-handle-producer-audit.md` still says that no producer/value contract was found for `IfTouchWork+0x64E/+0x08`, calls records `IfTouchWork+0x600+8*index`, and recommends observing records around `+0x600`. Replace those claims with the task callback producer and `manager+8*index+offset` layout while retaining the unresolved state-byte meaning, timing, and H2 handle relation.
- `h2-input-seam-contract.md` also says there is no producer for the panel/state fields and describes region records at `IfTouchWork+0x600`. It should link the new audit and preserve the distinction between a statically known producer and an unresolved semantic/runtime input contract.
- `milestones/H2-audio-settings.md` summarizes the producer of `IfTouchWork+0x64E/+0x08` as unresolved. Refresh that milestone summary after the independent review is accepted; keep physical mapping, callback cadence/order, actual H2 handle matching, and Azahar delivery unresolved.

These are findings for the coordinator to route; no dependent report or milestone file was edited here.

## Limits and evidence level

This is a static instruction review of the pinned image and bounded function spans. Task-factory linkage establishes a callback registration argument, not observed task execution cadence or ordering versus `TitleConfig_Calc`. The state-byte values and branch conditions do not identify event names, physical coordinates, or UI actions. The corrected record addresses do not settle whether H2's `-1` fields intentionally match the initialized active index or are changed by an untraced path. No runtime input or Azahar behavior is established.

Commands run, all read-only:

```powershell
python tools/split_asm.py --addr 0x0010299C
python tools/split_asm.py --addr 0x0010797C
python tools/split_asm.py --addr 0x0029D8FC
python tools/split_asm.py --addr 0x002B88C4
python tools/split_asm.py --addr 0x0010797C | Select-String -Pattern 'strb|strh'
python tools/split_asm.py --addr 0x002B88C4 | Select-String -Pattern 'add      r1, r1, r0|strh     .*\[r1|ldrsh    r0, \[r2, #0x4a\]'
```

No code, audit, milestone, board, tests, or runtime state was changed. No compiler, test, emulator, RSP/RPC, profile/game mutation, firewall, or OS-input activity occurred.
