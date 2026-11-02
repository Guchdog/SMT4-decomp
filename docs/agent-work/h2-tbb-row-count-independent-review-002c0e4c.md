# Independent review: `Tbb_GetRowCount` (`0x002C0E4C`)

## Recommendation

Approve the C++ reconstruction and the corrected final-VMA classification. The function returns zero for null table, non-`TBL1` magic, or zero row stride; otherwise it tail-branches to the original unsigned divider with `(payload_size, row_stride)` and returns its raw result. The fresh run passed 13 direct cases, five selector compositions, and all three mutation controls. Relocation, interworking, and the three affected-TU build records check out.

The earlier classification mismatch is resolved: `exact_matching=true` is now computed after applying the JUMP24 relocation. The final 56-byte body and full staged image match the original exactly. The ledger row is correctly `matching`, and the current README byte/function totals reconcile.

## Frozen inputs and fresh run

Recomputed all 18 run002 packet SHA-256 pins; all matched. The pinned original image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; candidate source hash is `0f7b9cf75c130c1329045658b00e8a49f1850ccfaa0ce06149225725b0b0d5a2`.

Ran the assigned fresh final-VMA experiment:

```text
python -B tools/h2_tbb_row_count_experiment.py --out build/agent-work/H2-semantic/h2-tbb-row-count-review-002c0e4c/run002/checks/fresh
exit: 0
```

The fresh `report.json` SHA-256 is `e4991623381d1b24801a7f6bac071259ee7ec1df5a09d260f048bb1eb4c38fbe`. It records 13 direct cases, five selector compositions, zero mismatches, all mutation controls detected, successful IPS replay, and `exact_matching=true`.

## ARM contract and behavior audit

I independently disassembled the pinned 56-byte ARM entry. It checks `r0` for null; loads `table->magic` and compares with `0x314C4254` (`TBL1`); loads `table+8` row stride and returns zero when stride is zero. On the valid path it loads `table+4` payload size into `r0` and tail-branches to `0x002C6C10`, preserving `(payload_size, row_stride)` as the divider arguments and returning the divider's raw `r0`. There is no local signed conversion or post-call normalization.

The C++ implementation uses the same null/magic/stride guards and calls `ui_func_002c6c10(table->payload_size, table->row_stride)`. The field widths are `u32`, and the zero-stride check prevents a divide-by-zero call. Direct cases cover null table, bad magic, zero stride, zero payload, representative quotients, and high unsigned sizes/strides. The unmapped pointer case at `0x00600000` faults identically in original and candidate; this is recorded as an observed fault, not accepted as valid table memory. All 13 comparisons match return, SP, callee-saved state, persistent memory, writes, dependency events, and faults.

The five compositions call the original `0x002AEA28` selector over synthetic TBCR/TBL1 structures with row count 5 and indices 0, 4, 5, 6, and `0xFFFFFFFF`. All match, returning the expected payload address for indices 0 and 4 and zero at/above the bound. Each reaches the original divider once with arguments `(0x50, 0x10)` and aligned SP.

## Controls, relocation, exact bytes, and affected builds

All three controls are detected: wrong magic literal, wrong zero-stride boundary, and swapped divider operands. The body occupies 56/56 bytes and contains one JUMP24 relocation at offset 40 to `ui_func_002c6c10` (`0x002C6C10`), whose bit 0 is clear. The pinned interworking report confirms the target starts in ARM state; the selector's BL into the row-count helper also targets an even ARM entry. The direct event traces report aligned SP when entering the retained divider.

The runner now resolves the branch relocation before computing `exact_matching`. Its resolved body is exactly equal to the original 56-byte slot; the staged image is byte-for-byte equal to the pinned original image. The slot IPS replays to that image and changes no bytes outside the slot. Staged image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; IPS SHA-256 is `05d74f5c393d50755a689a9e2f249d745e78695b488a46410923749a168098ca`; object SHA-256 is `133e61e32fb85685d9da38ea6322536ff68e5a14bdbb128906c94d0002c73907.

The affected-TU report records exit code 0 for `tbb_loader.cpp`, `leaf_batch24_b.cpp`, and `leaf_batch32_c.cpp` (3/3 ARMv6K builds). This is focused affected-TU validation, not a full build.

## Ledger and README reconciliation

The ledger row for `0x002C0E4C` is now `matching`, consistent with the relocated final body and staged image. Independently counted totals are 10,908 matching functions / 3,120,808 bytes, 51 non-matching functions / 17,816 bytes, and 8 matching spans / 484 bytes. Total mapped inventory remains 10,959 functions plus 8 spans and 3,139,108 bytes. README exact coverage is `(3,120,808 + 484) / 3,139,108 = 99.43245...%`, rounded to `99.4325%`; its non-matching total is 17,816 bytes. The H2 row correctly states that the final-VMA body remains byte-identical and retains the original ARM divider.

## Limits

The divider at `0x002C6C10` remains original, so this review does not reconstruct or independently prove its transitive implementation beyond the tested quotient cases and the pinned ARM observations. Selector compositions use synthetic but structurally valid TBB tables; live resource population, table lifecycle, downstream profile validity, and runtime H2/audio behavior remain unproven. The unmapped table pointer test faults in both versions, and arbitrary invalid memory is outside the approved domain. No emulator was run.
