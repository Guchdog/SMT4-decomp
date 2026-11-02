# `0x002B787C` (`AsdText_GetLineCount`) static contract

## Structured handoff

- **Task / owner:** `h2-asdtext-line-count-contract` / `h2_8d24_case12_review`
- **Report:** `docs/agent-work/h2-2b787c-contract.md`
- **Reference image:** `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` (3,633,152 bytes).
- **Function:** `0x002B787C`, 176-byte ledger span; function bytes SHA-256 `ac0d9fc82a609cef94037db5c83037bac614b139391a6f59fd631a57615c6b54`. **At this original-code audit snapshot, before the C++ conversion,** the ledger row was `matching` and `src/engine/leaf_batch42_c.cpp` had SHA-256 `4d288c9f99a0800243ca735ffb94337b206f9868c28df7e848e192983eebfa25`. The current production source differs and the current ledger classification is `non_matching`; see the [implementation evidence](h2-2b787c-implementation.md) and [function record](../function-records/0x002b787c.md).
- **Related callees:** `0x002AE6B0` (24 bytes, SHA-256 `39132c786b4f14598c98e9a6c68661fbc2a16fd0d449099dc040eafd2f88b29f`) and `0x002AE664` (76 bytes, SHA-256 `9a08149396d2a69f6c46775ebffc83c59cdd30f2d1fc9fa8cdcb04a121106f56`).
- **Evidence:** static pinned ARM and caller audit only. Compiled, ARM differential, caller execution, and runtime evidence are all `not_run`.
- **Recommendation / next action:** implement only after the line-table and mapping-table domains are provisioned and validated. Keep the two helper dependencies original unless separately reconstructed. Differentially exercise the handle gate, sentinel, all control-code classes, table delta mapping, and signed index limit; verify the three direct caller continuations.

## Raw ABI and local effects

The function is ARM-state code. Entry is one raw 32-bit word in `r0`, used as a handle pointer. It has no other explicit input arguments. The 24-byte prologue saves `r4-r8` and `lr`; the epilogue restores them and returns. No VFP is used. The result is raw `r0` from `r7`, a 32-bit counter/loaded halfword. The body makes no writes to the handle, text table, or lookup table; its only writes are its own stack save. Direct callees add no writes (their bounded effects are below).

The function reads, in order:

1. `word[handle+0x14]` as a nonzero gate. If zero, return `0` immediately. This word's value is not otherwise used. A null or unreadable `handle` faults here; the function has no null check.
2. `word[handle+0x0C]` as the initial table index and as the loop-bound base.
3. Literal `0x0000FFFF` as the end marker.
4. On each loop pass, `word[handle]` as the base of 32-byte records, then `halfword[base + index*32]` as the current code.

A null `word[handle]` is not checked. A valid scan therefore requires a readable handle and mapped table records for each index read, plus a nonzero gate word at `+0x14`.

## Per-record algorithm and termination

Initialize `index = word[handle+0x0C]` and `count=0`. For each record:

- Load the halfword code at `table_base + index*32`. If it equals `0xFFFF`, return `count` immediately.
- Call `0x002AE6B0(code)`. It returns 1 exactly for unsigned codes `0xF801..0xF88F`; otherwise 0. If it returns 0, do not change `count`; proceed to the common index advance.
- For a recognized control code, compute `code - 0xF801`:
  - Difference `0`: increment `count` by one, then common index advance.
  - Difference `1` (code `0xF802`): terminate immediately and return the current `count` without incrementing it.
  - Difference `0x19` (code `0xF81A`): increment `index`, load the next record's halfword into `count` (zero-extended), then common index advance. Consequently this special record consumes the following record's halfword as the count and then advances past that following record.
  - Any other recognized difference: call `0x002AE664(code)` and add its returned word to `index`, then common index advance. A missing mapping makes the callee return zero, so the common advance still moves by one.
- Common advance increments `index` by one, computes `limit = word[handle+0x0C] + 0x3E7`, and repeats only when ARM **signed** `limit > index` is true. Otherwise return `count`.

This gives two normal termination mechanisms: an encountered `0xFFFF` record; or exhaustion of the signed index bound. Under an ordinary nonnegative index with no 32-bit addition/wrap, the index check permits scanning indices below `start+999`; the code reads the current record before checking the bound. Recognized control values can skip extra indices through the mapping result. `0xF802` terminates before the index check. There is no separate explicit maximum on the lookup walk inside `0x002AE664`; it relies on its own sentinel.

The bound is a signed `BGT` test, not an unsigned comparison. The routine does not validate arithmetic overflow, negative/high-bit indices, table capacity, or presence of either sentinel. For arbitrary indices/table contents, a read can fault or the helper callee can continue searching indefinitely if its sentinel is absent. Do not claim general termination outside a valid initialized table and non-wrapping index domain.

## Direct callees

### `0x002AE6B0` — range predicate

The 24-byte body performs unsigned arithmetic only: `value -= 0xF800; value -= 1; return value < 0x8F`. Equivalently it returns one for `0xF801..0xF88F`, inclusive, and zero otherwise. It reads/writes no guest memory, preserves `r4-r11`, restores SP, and returns the predicate in `r0`. The caller already loaded a halfword, so its input is in `0..0xFFFF` for this use.

### `0x002AE664` — code-to-index-delta lookup

The helper saves `r4`, loads table base `0x00464DA8` and sentinel `0xF890` from its literal pool, then scans 16-byte records. It compares the record halfword at offset `+0` with the input code. On match it returns the word at record `+4`; on sentinel before match it returns zero. The caller adds this return value to its current index. The helper itself only reads its table and writes its stack save; it restores `r4` and SP. It has no explicit array bound or null check; table readability and the `0xF890` terminator are preconditions for guaranteed termination. The meaning and valid range of the `+4` delta are not established by this static audit.

## Direct callers and consumed return

A word-aligned ARM `BL` target scan of the pinned image found three direct call instructions to `0x002B787C`. Each callsite was decoded in context. This does not find indirect dispatch, Thumb/BLX call paths, or prove runtime reachability.

| Callsite / caller | Argument and return use |
|---|---|
| `0x00286AD0`, `0x00286928` | On the incoming helper `r2==0` path, after its `0x0028E974` call, the caller invokes this function when its normalized selector is 11 or 19. Thus raw selectors 11, 13, 14, and 15 (which normalize to 11) and raw 19 can reach it, subject to earlier branches. It passes `word[P+4]` in `r0`, where `P` is the selected work pointer. The returned count is stored to `word[P+0x20]`; it is consumed, not ignored. This is path-local static behavior; no captured runtime selector/state is attributed to this call.
| `0x001173F0`, `ui_func_00116954` (`src/engine/leaf_batch44_a.cpp`) | Passes `word[r5+4]` in `r0`. It saves raw `r0` return at `[sp+8]`. Later, in a row loop, it compares that saved value against the current row index and skips drawing when the signed comparison is `<=`. The return is therefore used as a line/count bound. The higher-level type/layout of `r5+4` is not assigned here.
| `0x002CF5F0`, `StatusDown_UpdateHelpMessage` (`src/ui/status_down.cpp`) | Loads the status-work pointer from `*[0x0044E190]`, then passes `word[work+0x22A0]` in `r0`. It moves the raw return into `r1` for `UiListCursor_Setup(work+0x22A8, count, 8, 1, 0, 1)`. This directly treats the result as a list line/count parameter. `StatusDown_UpdateHelpMessage_Draft` has a matching readable `AsdText_GetLineCount(work->text_handle)` call under `#if 0`; that draft is corroboration of intent, not executable caller evidence.

`src/camp/title_flow.cpp` contains no direct reference found in the bounded name/address search. `src/ui/status_down.cpp` declares the routine as `s32 AsdText_GetLineCount(void* text_handle)`; callers support a pointer-like `r0` and count-like return, while the machine contract remains raw 32-bit input/result. No evidence here establishes nullability, handle object lifetime, or the exact meaning/layout of the table and gate words.

## Static source and input identities

| Input | SHA-256 |
|---|---|
| `src/engine/leaf_batch42_c.cpp` | `4d288c9f99a0800243ca735ffb94337b206f9868c28df7e848e192983eebfa25` |
| `src/engine/leaf_matching.cpp` | `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2` |
| `src/engine/leaf_batch28_b.cpp` | `783bd98ee6eb1d26723d660c9ab258cfa6ff836565d6ea9d440d5e65315f79bb` |
| `src/engine/leaf_batch45_a.cpp` | `962c018c8c02971ed5bf77cca52685dcda4d7cc2634868e8e7640009ddb17dff` |
| `src/engine/leaf_batch44_a.cpp` | `f240510926c500cf928d42c3f7f46a6e0f461c53329663a2e8e1c27f55d102af` |
| `src/ui/status_down.cpp` | `4a34235f4e2eca511e8156420359dfd52ad739cdb5915e3e45f4c6bb2bc8c183` |
| `src/camp/title_flow.cpp` | `11b5360c77aecb4ab0e510774fd42a1cb479e8343aff4bb1a30d4cadeccc1b5e` |
| `config/functions.csv` | `e678207c1293d6fea8dba0a3b44531c6724457dddf1d75d3af8540318512312b` |

## Validation needed before implementation acceptance

A differential fixture should compare original versus compiled C++ at the helper entry with identical mapped handles, table records, lookup table and stack. Cover gate word `+0x14` zero/nonzero; early `0xFFFF`; `0xF801`, `0xF802`, `0xF81A`; all other values in `0xF801..0xF88F`; values immediately outside the recognized range; mapped/unmapped recognized values; and bound equality/one-before/one-after cases. Vary initial index, all count values used after `0xF81A`, lookup deltas, multiple mapping rows, and at least two deterministic memory seeds. Assert return, SP, `r4-r8`, ordered callee entries/arguments and no guest writes; record original fault/hang domains rather than claiming C++ null/fault parity without evidence. Negative controls should change the control range, sentinel, stride, `0xF81A` count source, `0xF802` termination, mapping delta, increment, signed bound, and gate behavior.

Caller compositions should exercise the three direct callers with controlled valid handles: `0x00286928` selectors normalizing to 11 and raw 19 on paths that reach the line-count call; `ui_func_00116954`'s line-row bound; and `StatusDown_UpdateHelpMessage`'s `UiListCursor_Setup` count. Compare the actual return consumer and caller-visible writes/continuation. These are proposed offline cases; no caller execution was performed here.

## Commands and results

Read-only commands/scripts used, each exited 0:

- Capstone ARM disassembly of `code.bin` at mapped addresses `0x002B787C` (176 bytes), `0x002AE6B0` (24 bytes), `0x002AE664` (76 bytes), plus relevant windows around the three callers.
- Word-aligned ARM `BL`-immediate scan for target `0x002B787C`; hits: `0x001173F0`, `0x00286AD0`, `0x002CF5F0`.
- `rg` searches over assigned source files and `config/functions.csv` for the address/name and the relevant caller symbols.
- SHA-256 and length calculation for image, function slices, and source/caller files.

No compiler, build, unit test, differential runner, emulator, or runtime trace was run. Remaining limits: malformed/unmapped handle/table behavior, bound arithmetic wrap/high-bit indices, missing sentinels, valid aliasing domains, indirect/Thumb callers, and runtime branch/input distribution. This report establishes the static raw contract only.
