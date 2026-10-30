# Independent review: `UiConfig_FillPair` (`0x0027EDF8`)

## Recommendation

Recommend acceptance of the **isolated helper contract** as supported ARM differential evidence for an aligned pointer to two writable ordinary-RAM words. The candidate behavior and reports are consistent with the pinned original. This recommendation covers only `0x0027EDF8`; caller composition, titleConfig initialization, task/UI behavior, persistence, production integration, and runtime remain open.

## Original contract and candidate

The pinned US v0.1.0 image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, matching `config/game_info.json` and both reports. `python tools/split_asm.py --addr 0x0027edf8` shows a 24-byte ARM helper:

- `0x0027EDF8`: `and r1,r1,#0xff`.
- `0x0027EDFC..0x0027EE00`: replicate that low byte across all four bytes of `r1`.
- `0x0027EE04` and `0x0027EE08`: store the resulting word to `[r0]` and `[r0,#4]`.
- `0x0027EE0C`: return with `bx lr`.

There are no source reads, calls, or global accesses. The observable write footprint is exactly eight consecutive bytes, `destination[0..7]`. The callee-saved register, SP, and VFP preservation requirements are ordinary ABI requirements; the caller does not consume the helper's return value or flags.

The candidate at `experiments/semantic_equivalence/h2_pair_fill_candidate.cpp` uses unsigned `u32` operations, masks `value & 0xFFu`, replicates via defined unsigned shifts, and writes `destination[0]` and `[1]`. It compiles as ARMv6K with no relocations according to the runner/report. Its domain is deliberately narrower than arbitrary pointers: `destination` must be aligned and designate two writable words in ordinary RAM. That is sufficient for the observed titleConfig caller's `work+0x1C` when the workspace base is suitably aligned; the allocation alignment guarantee itself belongs to the allocator/caller contract and is outside this isolated helper test. The candidate's `u32*` source signature is ABI-compatible at the register level, though any integrated declaration should use a consistent project-facing pointer type (the checked-in helper is declared with `u8*`/`void*`).

## Independent report review

Both run-001 reports are internally consistent and their important input identities recompute:

- Image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Candidate source: `d2f227f7c5675a81414b76027fbb7f1b531de2a08d0fd5de2a3ceef9ccda8d1d`.
- Candidate object in both runs: `fb7b1ca487057c8b2aafb097d3b99e29eb30c150503c92f0b1191ebd67ff66bd`.
- Compiler: Clang 23, `--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -ffreestanding -nostdinc -nostdinc++ -fno-exceptions -fno-rtti`.

For each seed (`7` and `20261024`), the report records 1,280/1,280 matches, no first counterexample, and `passed: true`: 1,024 directed combinations (all 256 low bytes crossed with four upper-bit patterns) plus 256 seeded full-width values. Thus high-bit insensitivity is directly covered beyond just the caller's `0xFFFFFFFF` input. Both runs test a negative control that writes only the first word; the `low-00-high-00000000` case detects it as a data-memory mismatch. The control is sensitive to the second-word store the contract requires.

The runner executes original ARM at `0x0027EDF8` and a compiled, relocation-free local candidate blob in an ARM11 MPCore Unicorn model. It resets input registers, randomizes ordinary RAM and stack, checks the original-vs-candidate continuation and memory, access footprint, and callee-saved registers/SP/`d8-d15`; it intentionally does not compare unconsumed `r0` or NZCV. This is appropriate for the helper's caller contract. The test source checks the complete byte-domain case count on seed 7 and checks the control on the second run; the seed-20261024 JSON independently records all 1,280 candidate cases passing.

The report's stated limits are accurate: it does not establish behavior for unaligned pointers, read-only/MMIO memory, invalid pointers, concurrent observers, or complete titleConfig behavior. The original uses ARM word stores; the candidate/test only claim ordinary writable aligned memory, which is the safe shared domain. No issue found in low-byte replication, access extent, negative-control sensitivity, report identities, or isolated ABI handling.

## Evidence boundary and next step

This supports the isolated `UiConfig_FillPair` semantic record/candidate, not a titleConfig replacement. The observed initializer caller passes `work+0x1C` and `0xFFFFFFFF`; the helper's supported contract predicts both adjacent fields become `0xFFFFFFFF`, but the pair-fill report does not execute or validate the initializer's caller window. Before production promotion, preserve a matching declaration at the call boundary, compile in the integrated object graph, verify the caller pointer/alignment contract, and run the owning H2 integration/caller comparison. Do not infer user-visible option initialization, task lifecycle, save behavior, or runtime equivalence from these helper-only reports.

No test/build/emulator command was run for this independent review; I inspected the frozen source and two hashed reports.
