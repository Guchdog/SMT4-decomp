# H2 callback contract audit: `0x00221168`

## Decision

The pinned ARM body establishes a small wrapper contract but does not support a typed C++ reconstruction yet. Its explicit input is a zero in `r0` to the first callee; two later global getters and the selected value returned by `0x00296F60` feed a final 820-byte helper. The callback returns exactly the final helper's `r0`. Pointer chains and the final helper's object/state contract remain unresolved. The run-017 trace observes the outer handler at `0x001A07CC` returning 2, but it does not resolve that wrapper's nested target. Therefore the trace does not show `0x00221168` running or returning 0.

## Frozen identity and method

The run-002 packet hash is `303873f861881ce3871ddd6b32b617961d838528486176b429abdb1b946981bf`. I recomputed every declared `input_sha256` entry: all 14 matched, including the original image `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) and the five source TUs. The callback is ledger address `0x00221168`, size 148, labeled `matching`, with source body at `src/engine/leaf_batch30_c.cpp:50-51`. No source or ledger edits were made.

I inspected the exact ARM instruction words embedded in that source against the pinned image identity and traced only its direct callees. The following is a static contract description, not a runtime execution of this callback.

## Instruction-level contract

The callback uses the ARM AAPCS register/stack convention: it preserves `r4-r7,lr`, reserves 12 stack bytes, and restores both before returning. It makes these calls in order:

1. At `0x00221174`, call `0x0028DF3C` with `r0=0`. That callee conditionally stores the input word to the literal-pool global at `0x0043E0BC` (`0x0043E0B8 + 4`) when `input+1 < 3`; here it stores zero. It returns without changing the callback's `r0` contract in a meaningful way because the callback sets `r0=0` again before the next call.
2. At `0x00221178`, call `0x00289640` with `r0=0`. This helper loads through `[0x0043DA28]`, then `[+0x20]`, then `[+0xD0]`. If this result is zero, the callback conditionally stores byte `1` at offset `0x30` through the pointer loaded from `[0x0043E188+8]`, and unconditionally stores byte `1` at offset `0x31` through that same pointer. It then loads a second pointer from `[0x0043E188+4]`; if nonzero, it stores byte `0x14` at offset `0xA11`. If the first getter is nonzero, the first branch's stores are skipped. These writes are evident, but the owning structures and byte-field meanings are unknown. The unconditional byte store requires a valid first pointer on the zero-getter path; the callback has no null guard for it.
3. At `0x002211B4`, call `0x0028686C` with no caller-set input beyond the current `r0`. The callee loads through `[0x0044DE98]`, then `[+0x20]`, then `[+0xC0]`; its returned word is saved in `r7`.
4. At `0x002211C0`, call `0x00296F60` with `r0=0`. Its 164-byte body selects a branch using values loaded from global/object memory, including a byte compared with 5, then returns through one of several table/conversion paths (or a default zero path). The result is saved in `r6`. The selector, tables, pointer validity, and result interpretation are not established here.
5. At `0x002211CC`, call `0x00289640` again, with `r0=0`. This second getter result is passed as `r2` to the final helper.
6. At `0x002211EC`, call `0x00286928` with `r0=r7`, `r1=r6`, `r2` equal to the second `0x00289640` result, `r3=6`, and two stack arguments `[sp]=1`, `[sp+4]=0`. The final helper's `r0` is left unchanged through stack teardown and `pop {...,pc}`, so it is the callback's return value. No local return normalization is applied.

The direct callees are in `src/engine/leaf_batch22_b.cpp` (`0x0028DF3C`), `leaf_batch21_b.cpp` (`0x00289640`, `0x0028686C`), `leaf_batch42_a.cpp` (`0x00296F60`) and `leaf_batch45_a.cpp` (`0x00286928`). The first four are short, inspectable helpers, but the data behind their pointer chains still supplies hidden state. `0x00286928` is a substantially larger downstream routine with many memory accesses/calls and is not reduced to a typed contract by this audit. The callback is therefore not a leaf behavior that can be copied as a self-contained scalar function.

## Runtime relationship and limit

The pinned run-017 runtime record has 12 top-level handler entries and 12 returns for task `0x08C0AA80`; ten ID-8 calls enter `0x001A07CC` and have recorded outer returns of 2. The matching wrapper source at `src/engine/leaf_batch25_a.cpp:2789-2821` calls an indirect function at `0x001A07FC`, tests its `r0`, and changes a zero result to 2 before returning. This makes a nested zero result a plausible static explanation for an outer return of 2, conditional on the observed wrapper path and exact code being active.

Run-017 records neither the nested function pointer/target nor its raw return; the runtime JSON has no nested-callback event fields. It does not connect that pointer to `0x00221168`. Thus “callback `0x00221168` returned 0” is **not observed**. The narrow valid statement is: if a later trace proves that the indirect call targeted `0x00221168` and its final `0x00286928` call returned zero, the wrapper's zero branch would produce outer return 2. The present evidence establishes neither antecedent.

Run-017 runtime report SHA-256: `9976f6f643dfb9ef08e084cd2d6a92bfebbb7e1826dde761a122810e6aade4a4`. The associated review says the trace was original-only, the capture timed out during a still-active State-2 loop, and H2 remains open. That report's run packet did not pin the runner source hash/arguments, which constrains reproducibility. No runtime or differential evidence for `0x00221168` itself was produced in this audit.

## Smallest useful next evidence

Use a separately pinned, read-only RSP observation at the already identified ID-8 wrapper: record the indirect target and raw `r0` at `0x001A07FC` and the wrapper return at `0x001A0800`, together with task pointer/handler ID. If the target is `0x00221168`, add bounded entry/return breakpoints for `0x00221168` and `0x00286928` to capture the six call arguments, relevant pointer-chain values, selected `0x00296F60` result, and final `r0`; do not infer names for fields. That single trace would establish whether this callback participates and the value that composes to 2. A typed C++ candidate still needs the layouts/contracts behind the globals and `0x00286928`, then contract-specific offline differential and caller validation.

## Evidence boundaries

- Confirmed statically: pinned callback instructions, direct call order, call registers/stack arguments, conditional byte/word stores, and direct final-return propagation.
- Bounded related runtime observation: outer handler ID 8 entered `0x001A07CC` and returned 2 ten times in run-017; its nested target/result were not captured.
- Not established: callback `0x00221168` runtime binding or return, meanings/types of object fields, validity of every indirect pointer in all states, behavior of the large final helper as a whole, physical-input parity, patched-side behavior, completion, persistence, or game-level effect.
