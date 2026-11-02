# Independent review: H2 resource-flag predicate `0x002A63F8`

## Recommendation and blocker

The candidate is semantically supported for the tested valid-resource domain, and the staged 24-byte slot/IPS are correctly scoped. The actual `TitleConfig_Calc` call slice is exercised with production inputs `(group=0x2F, subindex=0)` and its zero comparison. The resolver null behavior remains an unmapped read fault rather than being silently converted to false.

There is a classification blocker: `config/functions.csv` labels `0x002A63F8` `matching`, while the pinned report says `final_byte_identical:false`, gives a final candidate hash `2ee033ab...`, and the staging manifest classifies the replacement `non_matching`. The pinned original function span hash is `1a78f576...`; these identities differ. I did not edit the ledger/status under this review lease. Reconcile the ledger row before treating the candidate as promoted. For evidence outside that row conflict, retain a bounded `non_matching` recommendation.

## Frozen provenance, staged scope and relocation

All 25 declared packet inputs exist and match `task.json`. Pinned original image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Candidate source SHA-256 is `0406b1ec91f6cf0091f9b8ca57fbbaf35c3a42e420c28b9932f5d92c46cda198`; the existing candidate object hash matches manifest `2fb57fbbaddbc320221134bbec8be3f801d07e2924b75a1446472a0f47561c47`.

The staging manifest hash is `2df226682e405c6a2ece308342865794c145d13197091bd1a86f8606950aee0b`; staged image hash `818f8a104e1761860d3967789994990570838cfc2751d21ddca32caeb8c9cf8d`; IPS hash `652f61bfb85c751bc26a5abb12a22ebbd4b50d17f1fa85acc0bbf474c6e80de0`. I recomputed the base image SHA `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`, applied the IPS in memory, and confirmed it round-trips to the exact staged image. Exactly 12 bytes differ, all inside the declared 24-byte slot at VA `0x002A63F8` (file offset `0x1A63F8`). The replacement fills the full slot; no changes escape it.

The extracted pre-relocation body is 24 bytes, SHA-256 `b809f7258a32e18ed6ac5b506bbcd3a09a0e50a83bd3ed2a2d5a770f754f8fb4`, with one `R_ARM_CALL` relocation at offset 4 to `engine_func_002b96f0`. Resolved body/replacement SHA-256 is `2ee033ab1928a44ac336a9903c208fcd79724692e779ff082f95d31a338c46c2`. I decoded the staged `BL` `0xEB004CBB` at VA `0x002A63FC`; it targets the even ARM address `0x002B96F0`.

The staged image is built atop the run-013 combined H2 image, not directly from `code.bin`. The staged validation compares original `code.bin` execution against that staged image. For the tested slice, I independently confirmed that the base run-013 bytes at `0x001EA964..0x001EA978`, `0x002B96F0` (24 bytes), and `0x00145798` (16 bytes) equal the pinned original. This bounds interference from other combined-image changes for this exact path; it does not establish whole-image equivalence.

## Predicate and consumer ABI

Pinned ARM `0x002A63F8` saves/restores `r4,lr`, calls `0x002B96F0` with incoming `r0/r1`, reads `[record+0x10]`, masks bit 2 and returns exactly 0 or 1. The candidate uses `u32 ui_func_002a63f8(u32 group,u32 subindex)` and returns `(word & 4) != 0`; it preserves callee-saved state/SP and has no global writes. Its C++ body uses `r11` as the saved callee register instead of original `r4`, which is ABI-compatible. The resolver declaration/definition is also two `u32` arguments and a raw `u32` return. Consumer declarations found in the packet's sources consistently use the two-`u32` signature; assembly callers set `r0/r1` explicitly.

The resolver at `0x002B96F0` uses `table + group*24`, selects a 32-bit object pointer and tail-branches to `0x00145798` with the subindex preserved in `r1`. The tail helper returns zero for a null object pointer and otherwise produces the record pointer. The predicate then dereferences `record+0x10` without a null check. This is intentional: with an unmapped null-resolved record, the original and candidate both fault instead of returning false. A null table, invalid non-null entry, out-of-range group, invalid record pointer and lifetime violations remain outside the supported domain.

## Differential, controls and TitleConfig caller

The pinned differential report SHA-256 is `524113ee09307a4b85d7a4fcb3370499e5b43b0a392049acbbb6412e884884a9`. It lists eight valid cases covering `(0x2F,0)` with flag words clear, bit 2 set and all bits set; varied groups/subindices and unrelated bits; plus the null-result fault case. The valid case comparator checks result, ordered reads, ABI registers/SP, completion and faults; writes are omitted from the comparison key but checked for no writes outside the stack scratch range. Two compiled negative controls—bit mask 4→8 and predicate polarity inversion—are reported detected.

The TitleConfig slice in pinned ARM is:

- `0x001EA964`: `mov r1,#0`
- `0x001EA968`: `mov r0,#0x2F`
- `0x001EA96C`: `bl 0x002A63F8`
- `0x001EA970`: `cmp r0,#0`
- `0x001EA974`: `nop`; comparison branch follows at `0x001EA978`.

`titleconfig_caller()` starts execution at `0x001EA964` and stops just before that branch, recording `r0` and the CPSR zero flag. It runs original, final-VA candidate and staged image for flags 0, 4 and `0xFFFFFFFF`; reported rows match. The staged direct tests also execute the staged bytes rather than copying a candidate body into the original profile: the runner's `setup(image_bytes=...)` maps the supplied staged image at `0x00100000`.

One narrow null-fault trace gap: the runner executes `execute()` for staged null input and independently asserts a fault/read/no completion, but the explicit equality chain compares only `null_results[0]`, `[1]`, and `[2]` (original, temporary and final), omitting `[3]` (staged). Since the staged slot equals the final candidate and the base resolver/tail spans match original, the expected staged fault path is strongly implied; still, the report phrase “same fault behavior ... staged image” is not established by the direct equality expression. Record this as a small evidence/report limitation, not a semantic counterexample.

## Evidence limits and next action

- Compiled body and staging: hashes, slot fit, IPS round-trip and ARM branch were independently checked from read-only artifacts; I did not build.
- Offline differential: eight valid fixtures plus null fault and two controls are report claims; I did not run the runner.
- Caller: bounded pass for the actual `TitleConfig_Calc` call slice, not the whole TitleConfig state machine.
- Runtime: `not_run`; no natural resource lifecycle, scheduler path, or audio-settings scenario is established.

The staged candidate and specific caller slice are supported under valid mapped table/object/record preconditions, preserving the original null fault. Before promotion, correct the stale `matching` ledger row because final candidate bytes differ. The staged profile remains a one-slot nonmatching replacement; no claim is made for malformed pointers, concurrency, whole H2 equivalence or runtime.
