# Independent review — H2 logical mode-1 query

## Finding

The source-level helper is a sound, bounded reconstruction of the isolated pinned contract and supports isolated promotion with its current `non_matching` ledger label. The pinned instruction path and production C++ agree on unsigned `id < 31`, flag bit 0, the counter address, return values, and read-only effects. I found a narrow sensitivity gap in the report's invalid-ID boundary cases: ID 31's counter slot is left zero in the mapped page, so a mutant that erroneously accepts ID 31 can still return zero. The implementation's explicit `id >= 0x1f` guard is correct; strengthening that one directed case would make the invalid-bound evidence robust.

This review does not establish input producer cadence/freshness, physical control mapping, H2 event delivery, or integrated/runtime equivalence.

## Pinned behavior and ABI

I verified the pinned code image hash `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The 60-byte record span at `0x002BFFBC` contains the relevant instructions and literals:

- `cmp r0,#0x1f; bhs` rejects unsigned IDs `>=31` before either global access.
- The literal at `0x002BFFF0` is `0x004650A0`; loading `[base,#8]` reads the 32-bit mode flag at `0x004650A8`. `tst #1` returns zero when bit 0 is set.
- The literal at `0x002BFFF4` is `0x004E3C58`; the query loads `*(u32*)(0x004E3C58 + 4*id)`, compares it to exactly `1`, and returns the loaded comparison result (0 or 1).
- The helper uses only `r0-r1`, does not alter SP or write guest memory, and returns via `bx lr`; thus it preserves callee-saved `r4-r11` and stack balance under AAPCS.

The production implementation in `src/engine/leaf_batch32_c.cpp` matches those semantics and uses `s32 ui_func_002bffbc(u32 id)`. Its direct C-linkage declarations in the six caller TUs use the same `s32(u32)` ABI. `asd_model.cpp` and `asd_frame.cpp` also declare `UiInput_Trigger2(u32)` as returning `s32`; all eight TUs named in the compile report compiled successfully.

## Differential, controls, and artifacts

The differential report SHA-256 is `a972e29a7f9ddedba99c78645ff63c941d1364475832d7f284633c735dcabde3`; the pinned image hash in it matches. It records 496 valid calls for all 31 IDs × four flag values `{0,1,2,3}` × four counter values `{0,1,2,0xffffffff}`, plus ten selected invalid-ID calls for `{31,32,0x7fffffff,0x80000000,0xffffffff}` under flags 0 and 1. It compares return/fault/PC/SP and callee-saved registers; write hooks record no guest writes on original or candidate. No mismatch is recorded.

Both negative controls are meaningfully directed. With flags `1`, the wrong-flag-bit mutant returns 1 while the original returns 0. For ID 7, counter 7 is zero and counter 8 is explicitly seeded to one, so the wrong-index mutant returns 1 while the original returns 0. The report's invalid cases do not similarly prove the upper boundary against an off-by-one mutant: the runner seeds only IDs 0..30, leaving ID 31's adjacent mapped counter at zero. Recommended correction for a future refreshed differential is a direct `id=31, flags=0` case with the adjacent counter seeded to 1 (and, optionally, a sentinel/counter-page arrangement that makes accidental out-of-range reads observable). This is a sensitivity limitation, not a discrepancy between the pinned helper and production source.

The production compile report SHA-256 is `0bc49ccbfe7101a86c03329330316ff8bb4c9f0a5ffd8b242d346bc9a15dd1d4`. I verified all eight object files exist and their hashes match the report. The production definition object is 68 bytes and relocation-free; independently extracted candidate and production bodies are both 68 bytes with hash `0dfb38ba0a2c8384b0557230def99f875ad18866bc21a6eb5851b1ebf9f7fd8f`, with no relocations. The original span is 60 bytes, so `config/functions.csv` correctly retains `non_matching`; the 68-byte reconstruction is not represented as matching, and no patch-image/runtime claim follows from the offline evidence.

## Caller and producer limits

The H2 Calc contract and producer audit establish mode-1 calls using IDs 9, 0, and 1. Other engine callers pass additional IDs, so the recovered helper domain is IDs 0..30 while the H2-specific usage set is narrower. The table audit associates those IDs with rows and masks but expressly does not determine physical buttons or prove all 31 counter words are refreshed on each successful producer call. The query reads the mode flag at `0x004650A8`; producer availability at `0x004650A4` is a separate field. Neither this helper differential nor the consumer-TU compiles establish input delivery, producer scheduling/freshness, event ordering with Calc, safe event injection, an IPS image containing this non-matching body, or H2 runtime behavior.

## Recommendation

Accept only the isolated helper source contract with the truthful `non_matching` ledger classification and retain the producer/runtime caveats. For stronger invalid-domain differential coverage, add the ID-31 adjacent-counter sentinel case before describing the upper-bound behavior as mutation-sensitive across the invalid boundary. No build, test, emulator, RSP, or UI command was run for this review.
