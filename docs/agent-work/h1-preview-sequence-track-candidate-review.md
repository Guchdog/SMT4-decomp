# Independent review: `0x002B1C8C` preview sequence/track selector

## Review result

**Partial favorable review; retain as experimental pending integration and caller/runtime evidence.** I found no discrepancy in the pinned control flow versus the candidate over the defined valid-storage fixture domain. The critical `-2` distinction is confirmed in the instruction stream: row-next `-2` restarts the table track, while sequence-next `-2` enters the lookup scan as a signed selector and misses. The existing private differential report agrees on all 24 cases and detects the targeted duration-offset mutation. This review inspected rather than reran that report; no compiler or game runtime was used.

## Provenance and boundaries

All 14 input hashes in the review packet matched. The pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The helper body is `[0x002B1C8C,0x002B1DFC)`, 368 bytes, SHA-256 `8097eb2315dd6b7f6dd72be434ee38223841c6470bfa3b923b362900572ba092`. Static decode is contiguous across the full 368 bytes; prologue saves `r4-r7`, all exits restore them and return via `BX LR`; there are no direct calls.

Candidate source SHA-256: `cc7d7ab98919b4cabf741b09d95fb61f199246ddb79ac4e4f4a26f686e9fe007`. Linked candidate ELF SHA-256: `6e1c1591ed165215d50c2aff9780c4d16ed447b09e0d9be492b8e71285fd345d`. Existing run-01 report SHA-256: `e7a7f533ac1503ffec6f186b853b573a4bdfd4589de7e087dd9c715fdb1f7cdf`. These match the producer handoff identities.

## Pinned control flow and sentinel distinctions

The function first gates on byte `object+0x89` and the current table pointer at `+0x70`. It reads signed row index `+0x74`, signed progress `+0x76`, and the current 4-byte row's unsigned duration at `row+2`. ARM `ADDGT` advances progress only when duration is signed-greater than progress; since duration is unsigned-halfword zero-extended, this is equivalent to `duration > signed_progress`.

At the row-transition point, the code increments/wraps the index with `SXTH`, writes zero progress, and reads the next row's signed halfword. Crucially, `MOV ip,#0` at `0x002B1CCC` clears the scratch register before the subsequent sentinel branches:

- Next row `-1` enters sequence processing.
- Next row `-2` takes the restart branch: row index is reset to zero, the first row's signed selector is stored at object `+4`, `-1` at `+8`, and the function returns `object+4`.
- Any other row value, including `-3`, is an ordinary selected track value written at `+4`, with `-1` at `+8`; return is `object+4`.

Sequence processing has distinct sentinels. Current sequence selector `-1` completes immediately without advancing the sequence index. Otherwise the signed halfword sequence index advances with `SXTH` before reading the next entry's signed word at stride 28, offset `+8`. Next sequence `-1` or `-3` sets completion byte `+0x89` and returns the original object. Next sequence `-2` is **not** a restart or completion sentinel here: it proceeds as a signed lookup ordinal. Since the lookup's empty-entry count is nonnegative, `-2` cannot match. The scan therefore leaves `r1` at the cleared `ip` value, writes zero to current handle `+0x70`, and returns the original object. The earlier `MOV ip,#0` is why the tail's `MOV r1,ip` means null on a miss; this also explains zero-count behavior.

Lookup descriptor is at object `+0x48`; byte length is unsigned halfword `descriptor+6`, count is `length >> 2`, and the 4-byte record array pointer is `descriptor+0x18`. The scan tests the current sentinel count against the requested signed-16-bit ordinal before reading that entry. It increments the count when the record's signed halfword at `+0` is `-1`. On match it selects that 4-byte record pointer. A match resets row index/progress and bytes `+0x89/+0x8A`, stores the selected record's signed halfword at object `+4`, writes `-1` at `+8`, and returns `object+4`. A miss clears `+0x70` and returns the original object.

## Caller evidence

The H1 preview helper at `0x002BF9F0` executes `MOV r0,r4` at `0x002BFC40`, then calls `0x002B1C8C` at `0x002BFC48`. The next instruction reloads `r0` from `[r4,#0x86]`, so the callee's returned pointer is ignored. This is static caller evidence only; the encompassing H1 caller was not dynamically compared.

## Existing differential/report audit

The report identifies the same pinned image/body and candidate source/ELF hashes above. It records 24/24 cases passed, no first mismatch, and compares return `r0`, `r4-r11`, SP, stop/fault status, the mapped object/descriptor/lookup/sequence-region SHA-256, and caller-owned stack. The matrix covers early gates, duration/progress boundary and signed progress, ordinary row changes, row `-2` restart / row `-3` ordinary, sequence current/next `-1`, next `-3`, sequence-next `-2` miss, enabled/disabled/null sequence, lookup hits/misses, zero and non-multiple-of-four counts, signed row/sequence indices, and sequence-index wrap.

In the report, the sequence-next `-2` case preserves the old track values, leaves `+0x70=0`, advances sequence index to 1, and leaves `+0x89=0`; the candidate and original match. The distinct row-next `-2` case returns `object+4` with first row track selected. The negative control reads duration from offset zero instead of `+2`; it is detected with both `r0` and mapped-memory differences. Report and ELF hashes match producer handoff.

I did not rerun the offline Unicorn harness or focused test module under this read-only review assignment. The producer handoff records the final focused test run as passing; the two earlier failed assertion attempts are also disclosed there and were followed by a passing final run.

## Bounds and recommendation

The differential fixtures use valid, mapped, non-aliasing object, descriptor, row, lookup, and sequence storage. Original pointers and signed indices are unchecked. The evidence does not define invalid-pointer behavior, arbitrary out-of-range access, aliasing overlap, concurrent mutation, or the lifecycle/initialization of the real H1 object at scene `+0xD74`. No production integration, full build, dynamic encompassing-caller run, or game-runtime validation is shown. Keep the candidate experimental and require a separate integration/runtime task before treating H1 behavior as established.
