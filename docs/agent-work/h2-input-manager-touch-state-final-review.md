# Final independent review: H2 manager touch-state audit

## Recommendation

**Accept the synchronized producer and record-layout findings after correcting one field offset in the final manager audit.** The current audit's direct `manager+0x08` write-site list is complete for the inspected callback span, and the task-registration, both active-index stores, and record-base correction match the pinned ARM image. However, its summary says the zero-crossing clears at `0x00107FE8` and `0x0010800C` depend on `manager+0x670`; both instructions read/update `manager+0x674`. Correct that offset before final acceptance.

## Pinned-image verification

Original image: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Function spans use `config/functions.csv` at checkout base `1f1179b8cdf22c3e4a5343cb8a528fde64f5aaeb`.

- **Init and task link:** `IfTouch_Init` (`0x0010299C`) calls the allocator with size `0x680` and stores the returned manager through `0x0043DCB4` if that global pointer was null. It passes `0x00107CCC` as the task callback and `0x0010A28C` as the second callback argument to the task factory, with the name `TOUCH CALC`. It stores the returned task pointer at `manager+0`, then explicitly stores `-1` at `manager+0x64E`, 10 at `manager+0x64A`, and 0 at `manager+0x64C`. This verifies task registration and initial values, not observed callback scheduling.
- **Manager state byte direct stores:** exhaustive `strb` inspection of the function span containing `0x00107CCC` found these direct writes to `[manager,#8]` (callback base register `r4`):

  | PC | Store / condition confirmed by the adjacent instructions |
  |---|---|
  | `0x00107D88` | Store `r8` only after `camp_func_002C0144` returned nonzero at `0x00107D7C`; the successful-index path has set `r8=1`. |
  | `0x00107E4C` | Store `r8` when the computed distance compared at `0x00107E44` is greater than 8 (`BLS` to `0x00107E50` is not taken). |
  | `0x00107E68` | Store value 6 only when `camp_func_002C01B8(0,3)` returns nonzero (`MOVNE`/`STRBNE`). |
  | `0x00107E94` | Clear only when the helper at `0x00107E8C` returns zero (`STRBEQ`). |
  | `0x00107EE4` | Store `r8` only when the hit-test at `0x00107EDC` returns nonzero (`STRBNE`); `r8` is 2 on this path. |
  | `0x00107F04` | Unconditional clear on this dispatch path. |
  | `0x00107F5C` | Clear when the signed difference computed at `0x00107F50..0x00107F54` is below `-0x140`, as tested by `CMN r1,#0x140` and `STRBLT`. |
  | `0x00107FE8` | Clear after a negative `manager+0x674` accumulator is incremented and the result is nonnegative (`STRBGE`). |
  | `0x0010800C` | Clear after a positive `manager+0x674` accumulator is decremented and the result is nonpositive (`BGT` back to `0x00107FA4` is not taken). |

- **Active-index stores:** the only callback `strh` writes to `[manager+0x64E]` are `0x00107D8C` and conditional `0x00107EE8`. Both store loop index `r5` after their corresponding hit-test succeeds. Init separately seeds that halfword to `-1`. Getter `0x0029D8FC` reads it signed and returns `manager+8` only when it equals the argument; otherwise it returns zero.
- **Registration record address:** `camp_func_002B88C4` loads the insertion index from `manager+0x600+0x4A` (absolute `manager+0x64A`) into `r0`, but then computes the record base from the manager itself: `r1 = manager + (index << 3)`. The stores land at `manager+8*index+{0xA,0xC,0xE,0x10}`. The callback reader uses the same base. Thus `manager+0x600+8*index+offset` is not the record layout. The successful path returns the pre-increment index; capacity failure returns `-1`.

The final manager audit correctly lists all nine direct state-byte store PCs and both active-index write PCs. Its only identified substantive correction is the accumulator offset at the two zero-crossing clear sites: `+0x674`, not `+0x670`.

## Synchronized H2 notes and remaining limits

The current handle-producer audit, input-seam contract, H2 milestone, Calc candidate review/function record, Azahar touch-route audit, and integration-path contract now consistently distinguish the static producer from unresolved runtime semantics. They describe the callback as registered, the `-1` initialization and index/state writes as static facts, and region records as `IfTouchWork+8*index+offset`; none of those reviewed notes still uses `+0x600` as the record-array base or says no manager-state producer exists.

The remaining claims are appropriately bounded: the byte at `manager+8` has no proven event name; task registration does not establish cadence/order relative to H2 Calc; the relation between the callback's hit index and TitleConfig's three registration indices/four `-1` query values remains unresolved; physical touch mapping and CemuHook-to-title delivery are unobserved; no safe guest-state write seam, runtime input behavior, or original-versus-patched Azahar equivalence is established. The Azahar route note correctly treats CemuHook as a possible touch source only and leaves GDB/RPC observation and its firewall gate separate.

The older direct handle audit remains useful for the TitleConfig sentinel/caller analysis and is explicitly superseded on manager producer/layout facts. Its current manager references use the corrected addresses. The synchronized summaries therefore need only the `+0x674` typo fixed in the producer audit; no further stale producer or record-base claim was found in the assigned read set.

## Commands and evidence boundaries

Read-only commands used:

```powershell
python tools/split_asm.py --addr 0x0010299C
python tools/split_asm.py --addr 0x0010797C
python tools/split_asm.py --addr 0x0029D8FC
python tools/split_asm.py --addr 0x002B88C4
python tools/split_asm.py --addr 0x0010797C | Select-String -Pattern 'strb|strh'
python tools/split_asm.py --addr 0x002B88C4 | Select-String -Pattern 'add      r1, r1, r0|strh     .*\[r1|ldrsh    r0, \[r2, #0x4a\]'
```

This is static evidence from the pinned image and bounded function spans. No compile/build/test, emulator, debugger/RSP/RPC, network, OS input, profile/game change, firewall action, or edit to source, board, or synchronized notes occurred. This review report and its run handoff are the only outputs of this task.
