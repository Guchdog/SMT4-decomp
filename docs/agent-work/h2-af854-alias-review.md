# Independent review: alias-aware `0x002AF854`

## Scope and frozen evidence

Read-only review of the alias-coverage packet, production/candidate sources, runner, function record, original pinned function and preserved output. All `input_sha256` entries in run-001 match. Reference `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; preserved output SHA-256 is `d155919fa8b23b2f6be5c099cbb4bddf1999bd3508b3715bd193f2d04d5b86a7`. I inspected the runner output and existing objects but did not independently rerun either build or differential.

## Ordering counterexample and volatile scope

The pinned ARM sequence loads the list pointer, checks null, stores halfword `index` at `object+0x5C`, clears halfword `+0x5E`, clears bytes `+0x87` and `+0x8A`, stores the low byte of `mode` at `+0x60`, then loads the selected word and stores it at `+0x20`. The production C++ uses volatile for exactly those five pre-read stores and the selected word load. It leaves the initial pointer load and final value-dependent store ordinary. Source and compiled order therefore preserve the original read-after-write behavior while keeping volatile limited to the events that can overlap the list read.

The strongest demonstrated counterexample is `list == object+0x5C`, `index=0`, `mode=0`: the ARM code first writes zero to the low halfword at `+0x5C`, then reads the selected word from the same address, so the selected value is zero. The runner's all-nonvolatile ordering mutant is uniquely generated and must produce a different selected word for this fixture; this directly demonstrates why the ordered accesses need a compiler-visible sequencing constraint. The other tested list bases are `object+0x20`, `+0x58`, `+0x60`, and `+0x84`. Across those five bases, seeds 0, 17 and 4729 and modes 0, 1, `0x100` and `0xffffffff` produce 60 alias cases, all with index 0. The mode cases correctly distinguish full-word nonzero mode from the low byte stored at `+0x60`.

This volatile use does not supply thread synchronization, MMIO guarantees, invalid-memory/fault equivalence, or C++ object-lifetime/type-alias guarantees for overlapping typed views. The available ARMv6K O2 object and Unicorn evidence demonstrate this compiler's target behavior for the tested ordinary-RAM fixtures; they do not establish portable host semantics for arbitrary overlapping C++ subobjects.

## Object identity and test review

I independently extracted `candidate_002af854` from candidate object SHA-256 `516c5aed72c5738989545c9a83a9897be7c4358fa907df34954c81e76326d19d` and `battle_func_002af854` from production object SHA-256 `06a038ddcec0acffbf0b49de94125217bb06eb0ed9256ebeb8e6a3127021e162`. Both are 64 bytes, have no function relocations, and their bytes are identical. The original ARM body is also 64 bytes; candidate/production are intentionally `non_matching` relative to it.

The preserved runner reports 431/431 direct cases, 32/32 compositions through original `0x002B8D24` index 2 with two asserted calls, four standard mutants and the selected-word ordering control detected. The direct comparison observes raw `r0`, SP, `r4-r11`, object/list bytes and ordered writes. The direct alias matrix is narrow and reproducible; the wrapper composition uses disjoint external lists. The standard controls detect null-path inversion, mode selection, stride and return changes. The ordering mutant strips the volatile qualifiers and asserts both a behavioral mismatch and a changed selected word for `list=object+0x5C`, index 0, mode 0.

The raw ABI is three AAPCS words: object pointer, full 32-bit index, full 32-bit mode; raw return is the original object pointer. The runner exercises indices 0, 1, 2, 7, 19 and 127 plus seeded values below 128, and null list; it does not exercise wrapping indices, invalid pointers or every possible alias. Existing cross-TU legacy `void` declarations remain a separate ABI/type-consistency concern.

## Relation to `0x002B8D24`

The implementation now emits its ordered stores before its volatile selected load for any ordinary mapped address chosen by the list pointer; that source structure could preserve index-2/index-5 alias reads as well. The existing evidence, however, tests aliases only at index 0. `0x002B8D24` calls this helper with index 2 in its common cases and index 5 in case 12; its 32 caller compositions use disjoint lists. Thus the *measured supported alias set* does not yet establish that the documented `0x002B8D24` domain has widened.

For a concrete index-2 overlap, list base `subobject+0x44` makes the selected word `subobject+0x5C`, which the helper writes before reading it. For an index-5 overlap, list base `subobject+0x20` makes the selected word `subobject+0x5C`. Add these and other relevant offset-derived aliases through the real index-2/index-5 caller paths, including any cross-alias between the two sequential subobject calls, before removing the alias limitation from the `0x002B8D24` record. The C++ ordering appears designed to handle them, but those cases and their support domain have not been demonstrated yet.

Conclusion: the focused alias-aware `0x002AF854` change is sound for the tested fixtures, and the selected use of volatile is justified by the instruction order and detected nonvolatile control. It strengthens the helper's implementation-level alias handling but does not yet provide caller-specific index-2/index-5 evidence to widen `0x002B8D24`'s supported domain. Runtime, cumulative integration, invalid-memory, concurrency/MMIO, and portable object-model claims remain open.
