# Independent review: `camp_func_002aea28` profile selector

## Recommendation

Approve the typed reconstruction for the bounded raw profile-selector contract and the two exercised original caller slices. The fresh final-VMA run passed all 16 direct cases, both caller compositions, and all three mutation controls. Its three dependency calls preserve the original order and argument shapes; the compiled body fits the slot, all call targets are aligned ARM entries, and slot-only IPS replay passed. No candidate behavior counterexample was found.

This approval does not extend to real TBB/resource lifecycle behavior, caller paths outside the two slices, or audio/runtime equivalence. The TBB services return controlled values in these tests; a returned pointer is not thereby established to refer to a live profile in game memory.

## Frozen inputs and fresh run

Recomputed all 18 SHA-256 pins from the run002 packet; all matched. The pinned original code image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The pinned implementation source hash is `44f199600e3548baa2983e6e7c5b2e942ba0941fc23f111ee6d5c0722aba80e4`.

Ran the experiment in the private output directory:

```text
python -B tools/h2_profile_lookup_experiment.py --out build/agent-work/H2-semantic/h2-profile-lookup-review-002aea28/run002/checks/fresh
exit: 0
```

Fresh report SHA-256 is `1cd86a0db7e64d58e0f07a9ef2b2b67aeb83ab2eddeecd6f5c4f8d3b6f428764`. It records 16 direct final-VMA comparisons with zero mismatches, two caller slices equal to the original, three detected mutations, successful IPS replay, and no changed bytes outside the entry slot.

## ARM and C++ contract audit

The pinned 56-byte ARM entry at `0x002AEA28` saves `r4-r6/lr`, preserves the full input index from `r0`, and makes these calls in order:

1. `Tbb_GetGlobalSubTable(14, 0)` — original `mov r0,#0xE; mov r1,#0`.
2. `Tbb_GetPayloadData(table)` — with the first call's raw `r0` result.
3. `Tbb_GetRowCount(table)` — with the same saved table pointer.

The original compares the unsigned 32-bit index against the unsigned 32-bit row count. `HS` returns zero; `LO` computes `payload + (index << 4)` directly into `r0`, so the stride is 16 bytes and the address arithmetic is 32-bit ARM arithmetic. It then restores the saved registers and returns the raw result. It has no early null check: null table/payload outcomes flow through the dependencies and final compare/add sequence.

The candidate retains the typed calls in that order and uses a compact inline ARM sequence with `cmp`, `movhs r0,#0`, and `addlo r0,payload,index,lsl #4`. Its `u32` index/count and integerized payload preserve the unsigned bound and 32-bit result computation without C++ pointer arithmetic. The 16 direct fixtures cover zero/one/count boundaries, count-1, count, count+1, high-bit values, `UINT32_MAX`, zero table, zero payload, and large count/index combinations. Original and staged results, call arguments/order, SP/callee-saved state, writes, and faults matched.

The fresh report's two caller slices execute the original setup and call instructions for request `0x99` at `0x002F4DEC` and request `0xDC` at `0x00286B7C`, then stop after the call. Both matched, and all 14 recorded calls in each trace were stack-aligned. The traces preserve both selector invocations with `(14,0)` and the expected table pointer arguments; the surrounding wrapper's other dependencies are controlled stubs.

## Controls, relocation, and placement

All three mutation controls were detected: wrong subtable ID, stride 8 instead of 16, and a wrong equality boundary. The compiled body is exactly 56 bytes, byte-different from the original, and has three branch relocations:

- offset 16 → `Tbb_GetGlobalSubTable`, `0x002C0EC4`
- offset 24 → `Tbb_GetPayloadData`, `0x002C0E9C`
- offset 36 → `Tbb_GetRowCount`, `0x002C0E4C`

The fresh report marks all target bit-0 values clear. The independently pinned interworking report shows each target begins with ARM instructions; the surrounding caller BLs also target even ARM entries. Dependency calls report aligned SP. The one-slot IPS replays to the staged image; a full byte comparison found no changed bytes outside `0x002AEA28..0x002AEA5F`. Staged image SHA-256: `6141b0870c48ace1433ee58f879e96956514e94643455ab18ad6183c71c65f7e`; IPS SHA-256: `6a55019fcf43bc8773f61b809d06ebb5902136f8f1608a17a0f82dd7c03ed990`; object SHA-256: `b2094d907e950c4a6ad73e68a146d08ca79f4b94cb5371b36a5e3c51e0d61f46.

The pinned affected-TU report records successful ARMv6K compilation for `leaf_batch24_b.cpp`, `leaf_batch32_c.cpp`, and `tbb_loader.cpp` (3/3 exit codes zero). This is the focused affected-TU check, not a full build.

## Ledger and README reconciliation

The ledger labels `0x002AEA28` `non_matching`, consistent with the report's `exact_matching=false`. Independently counted ledger totals are 10,908 matching functions / 3,120,808 bytes, 51 non-matching functions / 17,816 bytes, and 8 matching spans / 484 bytes: 10,959 functions plus 8 spans and 3,139,108 bytes total. README totals reconcile: exact bytes are `3,120,808 + 484 = 3,121,292`, or 99.4325% of 3,139,108 bytes; non-matching bytes are 17,816. The H2 milestone and README accurately describe 16 direct cases, two caller slices, three controls, three ARM relocations, controlled TBB results, and the absence of runtime proof.

## Limits

The TBB global-table, payload, and row-count helpers are controlled hooks in this experiment; their full resource lookup/lifecycle and live TBB data are not validated. The wrapper fixture only establishes behavior for the tested dependency return values. A returned address from a high index/count combination is an observed raw 32-bit result, not evidence that the address is a valid profile object for later dereference. The two caller slices do not establish natural callback reachability or the rest of `0x002B8B78`'s state machine. Invalid/unmapped pointers, TBB resource population, manager lifecycle, actual profile semantics, audio output, and emulator/runtime behavior remain unproven.
