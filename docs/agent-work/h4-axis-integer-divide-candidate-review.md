# Independent review: experimental `0x002C615C` quotient/remainder candidate

## Disposition

Accept the candidate's bounded direct return-register evidence for the tested signed 32-bit input space as extended by the fresh run below. The unsigned long-division loop, modular sign restoration, divisor-zero return packing, 64-bit AAPCS return, and relocation-free compiled body are supported by source inspection and compiled execution. Do **not** interpret this as full machine-state equivalence or promotion approval: original and candidate have different stack writes, flags/full memory/stack-fault behavior are outside the comparator, and selector caller composition and production/runtime behavior remain untested.

## Frozen input and compiled identity

All 16 declared input hashes match the run-001 packet. The pinned `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Frozen candidate source SHA-256 is `970e00f3c6bf8e350f935158b5b8bab46919f257418f5efb0174d2b19e8da96b`; frozen runner snapshot SHA-256 is `9401f62e9e4072c80f8b93f89e51ac560eb0e3a73c1075ca0c3260f940c5fdc6`; original seed-20261028 report SHA-256 is `2350c505584f9d8322da4724eb936a0833c43b27331b0520b4e537bb89b27479`.

The run-001 compiled candidate was 128 bytes and reported object SHA-256 `29c52adaa8abc61a7906c3b79e471f0005a45c7742bd21f4957f40856f552a64`, candidate bytes SHA-256 `706c8a2a817b86e8e6ee1026d0c8a66ba9b605e58adfb6774d3ffee5a53ddd51`, and no relocations. The fresh independent compile reproduced the same object and candidate-byte hashes. I extracted the function from the ELF object and confirmed an empty relocation tuple; its ARM disassembly contains no calls or relocation back to `0x002C615C` or an integer divide runtime helper.

## Algorithm, result ABI, and edge behavior

The candidate first handles divisor zero by returning `u64(dividend)<<32`; with AAPCS32 little-endian scalar return this gives quotient bits in `r0=0` and original dividend/remainder bits in `r1`. For nonzero divisors it uses unsigned modular magnitude conversion, a 32-iteration restoring quotient/remainder loop, then modularly negates quotient iff signs differ and remainder iff the dividend was negative. There is no signed C++ overflow or `/`/`%` in the candidate. For signed 32-bit inputs the magnitude is at most `0x80000000`; at each loop step the shifted remainder is bounded by the processed input prefix, so the unsigned 32-bit shift/subtract loop is valid for that domain.

The compiled ARM object implements a true scalar return: `r0` carries quotient and `r1` carries remainder. The fresh differential includes representative `(17,5) -> (3,2)`, `(17,0) -> (0,17)`, `(0,0) -> (0,0)`, and `(INT_MIN,-1) -> (0x80000000,0)` outputs. The last is the pinned instruction result as a bit pattern; this review makes no C++ language-policy claim for signed division overflow. The candidate's zero case returns before its normal prologue; the disassembly shows that fast path directly.

## Differential and mutation review

I reran the frozen runner snapshot with routes rebound in memory to the repository root, pinned `code.bin`, and frozen candidate source. Fresh output: `build/agent-work/H4-semantic/h4-axis-integer-divide-candidate-review/001/checks/seed-20261029-rebind2/report.json`, SHA-256 `4d06d0788376036103006aa20222683059f2ea7c07af7cdd3777d1d3990e22e4`.

The run used 121 directed Cartesian input pairs from `{0,1,2,3,5,17,INT_MAX,INT_MIN,INT_MIN+1,-5,-1}` plus 512 deterministic random 32-bit pairs (seed `20261029`), total 633. Status was `passed`, with zero differences in `r0`, `r1`, `SP`, `r4-r11`, return-to-sentinel, or fault status; all 633 rows returned, restored the initial SP and preserved the initialized `r4-r11`. There were no non-stack writes. The mutation control replaced only the candidate's divisor-zero return with zero and reused `(17,0)` on original and mutant; it detected the changed remainder (`r1=17` versus `r1=0`).

The first invocation of the frozen snapshot exited 1 because its copied `ROOT` still resolved under the snapshot directory and clang could not find `ROOT/experiments/...`. I discarded that attempt and reran from a distinct fresh output after rebinding `ROOT`, `CODE`, and `SRC` in `main.__globals__` without changing snapshot bytes. The successful output and hash above are from that second invocation.

## Stack and observation limits

Stack writes differ materially and the runner intentionally does not include them in its equality keys. For original divisor zero, the trace records two 4-byte writes at `SP-8` and `SP-4` for dividend and LR; candidate zero path writes no stack. Candidate nonzero path begins with `PUSH {r4,r5,r6,lr}` (16 bytes), while the original normal path has no explicit stack write. Both restore SP in the mapped test setup. These differences can affect stack guard/fault behavior or observers of stack memory, so zero return differences do not establish full machine-state equivalence.

The runner records no faults under its mapped code/data/stack setup and checks `r0/r1`, SP, `r4-r11`, return, and non-stack write presence. It does not compare flags, all scratch registers, full memory snapshots, exact stack contents, stack boundary/fault behavior, caller composition, valid calibration inputs, production integration, or runtime behavior. The mutation control is one negative case, not a broad adversarial mutation campaign. These boundaries are properly stated in the frozen candidate report; the fresh run does not widen them.

## Review result

No algorithm, relocation, result-register, mutation, or report-overclaim defect found within the inspected domain. Keep the stack mismatch explicit and retain the candidate as experimental until selector-0/1 caller composition, stack/fault/flag scope, and production integration receive their assigned evidence. No candidate/source/runner changes, emulator/GDB, private save/profile access, or guest writes were performed.
