# Independent review: H2 logical-input flag refresh audit

## Recommendation

**Accept the core static counter path with two clarifying corrections to the report.** The pinned instructions support the stated 31-counter writer and its relationship to the mode-zero input queries. I found no contrary direct evidence that changes the bounded conclusion or justifies assigning physical input meanings. The report should add (1) the input-state-valid gate before reading each state word and (2) the `camp_func_002C1830` fallback IDs for Calc's `(4,0)` and `(3,0)` queries. It should also make the alternate `0x004650A8 & 1` path explicit for mode 0.

## Verified instruction path

Pinned image: `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; function table: `config/functions.csv` at the task's pinned checkout base.

- `TitleConfig_Calc` at `0x001EA928` calls `camp_func_002C1830` as `(9,1)` at `0x001EAABC`, `(4,0)` at `0x001EABDC`, `(3,0)` at `0x001EAC20`, `(0,1)` at `0x001EAE64`, and `(1,1)` at `0x001EAF14`. These are logical IDs/modes; the listing does not name physical controls.
- `camp_func_002C1830` (`0x002C1830`) dispatches mode 0 to `ui_func_002B902C`, mode 1 to `ui_func_002BFFBC`, and mode 2 to `ui_func_002C17D4`. It also makes fallback queries when the primary result is zero: ID 4 mode 0 can query ID `0xD`; ID 3 mode 0 can query ID `0xC`. The report's last bullet names IDs 4/3 but should surface these downstream queries. This behavior is also consistent with the prior input-seam contract.
- Both `0x002B902C` and `0x002BFFBC` reject unsigned IDs `>=0x1F`. When `*(u32*)(0x004650A0+8) & 1` is clear, they read `*(u32*)(0x004E3C58 + 4*id)` and return it unchanged only when it equals one; otherwise they return zero. With the bit set, `0x002BFFBC` returns zero. `0x002B902C` zeroes `r0`, compares it against the unsigned dword at `0x004650A0+0xC`, and returns zero on the emitted `BLS` path; that comparison is taken for every 32-bit threshold value. The subsequent helper-call block appears unreachable under this unsigned condition. The report's counter statement is correct as scoped to the clear-bit path; no functional claim is made for the apparent dead block.
- `func_001078D8` (`0x001078D8`) calls `func_0011C5EC` with first argument `*(u32*)0x004650A0` and second argument `0x004E3C28`. It sets the dword at `0x004650A4` to 1 iff that call returns nonzero, else zero. The loop then uses that dword as a gate. For each of 31 entries it reads a first-word record at `0x004099C0 + 8*i`, a second-word mask at `+4`, tests that mask against the same fixed state word at `0x004E3C28`, and updates a counter at `0x004E3C58 + 4*i`.
- **Correction needed in report:** if the record's first word is zero, the writer loads the corresponding state word only if the valid flag at `0x004650A4` is positive. When the input-state call failed/returned zero, `ip` remains the zero first-record word, so mask testing cannot match and the counter is cleared. When the first record word is nonzero, it is forced to zero before the mask test, likewise clearing the counter. Only the zero-first-word plus successful-input path can increment on `state_word & mask != 0`; otherwise it clears. The report describes the zero-first-word path as testing the state word without this condition. Add the condition to avoid implying stale/unavailable buffer contents are consulted.
- Under that successful zero-first-word path, matched bits increment the counter and nonmatches reset it to zero. This makes a `counter == 1` query a possible one-refresh pulse, but scheduling and number of refreshes between Calc ticks are not established; the report correctly labels this an inference and leaves callback scheduling unresolved.
- `engine_func_0010B578` starts with direct calls `0x0010B57C -> 0x001078D8` then `0x0010B580 -> 0x00108B10`. A later image-wide ARM review found a direct caller of this wrapper at `0x00101B8C` inside `crt_func_00101308`; the earlier bounded caller audit missed it. This establishes a static caller only; computed callback registration, Thumb spans, actual runtime scheduling, and outside-ledger code remain open.

The literal-reference scan in the report is consistent with the inspected writer/getter paths. Its stated omission of Thumb spans and computed targets is material and properly disclosed. Its potential mapping-row references and masks can be confirmed statically as table data, but that would not by itself prove device semantics or an Azahar injection seam.

## Bounded disposition and safety boundary

The report appropriately distinguishes the query-counter writer from the touch-halfword mismatch and does not claim physical mapping, callback scheduling, safe guest-state writes, or Azahar behavior. The references to `0x004E3C28`, `0x004E3C58`, `0x004099C0`, and `0x004650A0` establish static buffers/tables and control flow only. Do not write these addresses through RPC or other runtime control based on this evidence. Keep physical/source selection, row meanings, event refresh order, and any safe synchronized injection point unresolved.

No report or candidate edits were made. This review used only pinned-image disassembly, a bounded static xref scan, and the existing contract/report. No compilation, tests, emulator, RSP/RPC, keyboard/mouse, profile/game write, or firewall action occurred.


## Run-002 focused follow-up

The two requested corrections are present and match the pinned listing:

- `func_001078D8` stores an availability dword at `0x004650A4` from the nonzero result of `func_0011C5EC`. In the zero-first-word record case, the fixed state word at `0x004E3C28` is loaded only when this availability dword is positive. A later H4 pointer-trace review confirmed the state pointer is initialized once and never advanced inside the loop; the prior `+4*i` description was incorrect.
- `camp_func_002C1830` sends `(4,0)` to primary ID 4 and, when that result is zero, its case path invokes mode-0 ID `0xD`; likewise `(3,0)` can fall back to ID `0xC`.
- The mode-0 flag-set note is accurate: `ui_func_002B902C` sets compared `r0` to zero, compares it to the unsigned threshold dword, and takes `BLS` to return zero for every 32-bit threshold value. The following helper call appears unreachable on this emitted path. `ui_func_002BFFBC` directly returns zero when the flag bit is set.

**One further correction is required in the audit's refreshed writer summary.** It currently says “a missing bit or unavailable state resets [the counter] to zero.” In the pinned loop, when the first mapping word is zero and the availability value is zero, `0x00107948` executes `cmp r5,#0`; the conditional load and branch to the mask/reset block at `0x00107928` are skipped, and control proceeds to the loop increment at `0x00107954`. No store to that counter occurs on this path, so the prior counter is retained. The report should say: a valid state word with a missing mask bit resets the counter; unavailable input leaves the counter unchanged for zero-first-word records; nonzero first-word records reset it. A stale counter equal to one can therefore persist across an unavailable refresh, so the one-refresh pulse inference is conditional on successful refreshes and the observed schedule.

Recommendation: retain the two verified corrections and correct this unavailable-state effect before accepting the producer summary. Physical mapping, scheduler timing, runtime synchronization, safe injection, and Azahar behavior remain unresolved. No code or audit-report file was changed by this review.

## Run-003 final verification

The corrected audit now states the unavailable-input behavior accurately. In `func_001078D8`, a zero first mapping word branches to the availability check; when `0x004650A4` is zero, the `ldrgt` and `bgt` that enter the mask/reset block are skipped, and the loop advances without storing the counter. Thus availability false leaves that counter unchanged; the mask match/increment and missing-bit reset logic runs only after a successful state read. Nonzero first-word records still take the reset path.

The pulse statement is now appropriately qualified: `counter == 1` is consistent with a one-update pulse only on successful refreshes, and observable behavior depends on refresh scheduling relative to Calc. The audit also retains the successful-input availability gate, `(4,0)->0xD` and `(3,0)->0xC` mode-0 fallback paths, and the alternate mode-0 flag-set note. The pinned `ui_func_002B902C` listing sets the compared `r0` to zero and takes unsigned `BLS` to return zero for every 32-bit threshold; the later helper block appears unreachable on that path.

**Recommendation: accept the corrected static producer summary within its stated scope.** No remaining correction was found in the requested conditions. This review does not establish input mapping semantics, callback scheduling, runtime ordering, safe injection, or Azahar behavior. No builds, tests, runtime controls, or changes to the audit/board were performed.
