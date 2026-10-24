# Group #21 — fixed two-word initializers

## Finding

The two functions form a supported semantic family. Both execute the same
five-instruction ARM pattern: advance `r0` by a fixed offset, write the adjacent
words `1` and `0`, and return the adjusted pointer in `r0`. The offsets are
`0x04` for `0x00399D4C` and `0x14` for `0x003ABCF4`. This is a behavioral
reconstruction, not an exact-byte match: each compiled C++ candidate is 24
bytes versus 20 bytes of original ARM.

This finding covers aligned ordinary RAM whose full 8-byte output range is
mapped. It does not claim safety for unaligned addresses, MMIO, concurrent
observers, or a fault partway through the stores.

## Static contract and context

`tools/split_asm.py --addr` confirms both bodies are ARM-state, 20 bytes, with
no calls or literal-pool references. The ledger currently labels both rows
`matching`; the experiment leaves the ledger and exact wrappers unchanged.

| Address | Writes | Return | Caller/table evidence |
|---|---|---|---|
| `0x00399D4C` | `[base+4]=1`, `[base+8]=0` | `base+4` | Direct BL sites `0x001924DC` and `0x00276C04`; each is preceded by `add r0,r4,#0x40`. Both setup-plus-call windows were executed. |
| `0x003ABCF4` | `[base+0x14]=1`, `[base+0x18]=0` | `base+0x14` | Pointer at `0x004024D8` in a three-entry table has zero-valued neighbors and points to this function. No direct BL caller was found by a bounded aligned ARM BL scan. The indirect dispatch path is not executed. |

The direct call windows establish argument setup, return to the expected
continuation, and matching observable memory. In isolation, tests separately
check the return value and AAPCS callee-saved state (`r4-r11`, `SP`, `d8-d15`).
The original has no calls, and neither body touches globals or stack. The input
pointer is required to be word-aligned and point into mapped writable ordinary
RAM; null, unaligned and faulting pointers are outside the tested domain. The
two adjacent stores do not create a source/destination aliasing case.

The C++ candidate uses volatile word stores to preserve the two observable
writes and their order. The experiment compares the full data image, live stack,
return, callee-saved state, stop PC, and byte-level read/write footprints. NZCV
is not part of this leaf's ABI contract and is not consumed by the measured
caller windows.

## Differential evidence

Runner: `tools/fixed_pair_initializer_experiment.py`; candidate source:
`experiments/semantic_equivalence/fixed_pair_initializer_candidates.cpp`.
The original ARM bytes are executed from the pinned code image, independently
of the compiled C++ candidate. Each run tests 4,096 seeded random valid memory
and register states per function, plus three initial-field cases (distinct
values, zeroes, and all ones): 4,099 cases per function per seed. Two seeds
passed: `20261024` and `7` (16,396 function-case comparisons total). Each seed
also passed both validated direct caller windows and detected all three
negative controls: wrong offset, wrong second word, and wrong return pointer.

Reproduce from the repository root:

```powershell
python -m unittest tests.test_fixed_pair_initializer_experiment -v
python tools/fixed_pair_initializer_experiment.py --code extracted/exefs/code.bin --samples 4096 --seed 20261024 --output build/semantic-equivalence/group-21/seed-20261024
python tools/fixed_pair_initializer_experiment.py --code extracted/exefs/code.bin --samples 4096 --seed 7 --output build/semantic-equivalence/group-21/seed-7
```

Both test and runner commands exited successfully. The targeted test suite
passed 2 tests. Environment: branch `codex/semantic-equivalence-experiment`,
base revision `422c7afa52a337036caa82dca9136f30dbf8e891`,
`clang version 23.1.3 (MSYS2 package build)`.

| Artifact | SHA-256 |
|---|---|
| Pinned reference code | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Candidate source | `fe03a6aaf6863053891e49dd9f34ad00bcd14577166502f0632d2e89ce61c7c1` |
| Compiled candidate object | `dfa45521d7434a3e985d7558688f1e5a62eafa1517f2d4ad6dea71357731728a` |

Full machine-readable results are in the ignored run outputs
`build/semantic-equivalence/group-21/seed-20261024/report.json` and
`build/semantic-equivalence/group-21/seed-7/report.json`.

## Decision and limits

Accept this pair as `probada_arm` within the domain above; keep the existing
exact wrappers and `matching` ledger labels untouched. This does not establish
exact byte equivalence, execute the indirect table route for
`0x003ABCF4`, test a live game/emulator, or prove all possible states. No
production integration or caller window for the table dispatch is claimed.
