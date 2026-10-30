# Helper plus row-setter composition differential

## Result

The private offline Unicorn comparison passed all 8 listed composition cases.
The original side executed pinned `0x002BF9F0` and the real pinned
`code.bin` body at `0x002BDAC0`; the candidate side linked the unchanged
`h1_preview_helper_candidate.cpp` and `h1_animation_row_setter_candidate.cpp`
through a private adapter. Both actual setter call paths inside the helper were
exercised: the next-word `-2` restart path and the ordinary-next path. The
setter arguments, final mapped memory, return `r0`, callee-saved GPR/VFP state,
SP, caller-owned stack, and named external-call order matched for these cases.
The setter negative control was detected by the final-memory comparison.

The input-image hash is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
pinned helper span `[0x002BF9F0,0x002BFC88)` (664 bytes) hash is
`9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`; the
pinned setter span `[0x002BDAC0,0x002BDB2C)` (108 bytes) hash is
`e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a`.
The report records candidate/helper/setter/adapter hashes, ELF hashes, symbol
addresses, compiler invocations, and the extracted text hash.

## Cases and checks

The eight passing cases cover a valid object with a null row-table pointer;
an endpoint with sequence disabled; an endpoint that restarts via next word
`-2`; an endpoint that advances to an ordinary next animation; interpolation
setup with each direction; nonzero row mode bypassing sequence processing; and
an enabled feature with a null sequence pointer. The row table and sequence
arrays are explicit valid, non-overlapping synthetic memory. The sequence
fixtures include the expected `0x1C` entry stride and signed frame bytes.

The missing-`+0x50` animation-index store control is compiled from a private
mutated setter-source copy. The ordinary-next case changes the requested row
index from 0 to 2; omitting the store leaves object `+0x50` different from the
pinned original, and the projection reports `object/table/sequence memory differs`.
The control does not modify the existing candidate.

## Evidence boundaries

Only four of the helper's five callees are stubs: interpolation at `0x002C615C`
returns zero; `0x002B1FC0`, `0x002B1DFC`, and `0x002B1C8C` are no-op stubs. Their
effects and transitive behavior are unresolved. `0x002BDAC0` is not stubbed on
the original side; its pinned body executes, and the editable setter C++ runs
on the candidate side. The projection compares the final full synthetic data
mapping, return value, setter/stub argument and order traces, `r4-r11`, `d8-d15`,
SP, and caller-owned stack. It does not compare every caller-saved scratch
register or flags, memory access multiplicity/order, real asset bindings, or
H1 construction/lifecycle. This is not a runtime/game equivalence claim.

The successful command was:

```powershell
python tools/h1_preview_row_setter_composition_experiment.py --output build/agent-work/H1-semantic/h1-preview-row-setter-composition/overnight-20261025-row-setter-composition/results-v4
```

It exited 0 and reported `PASS 8/8; setter control=detected`. The report is at
`build/agent-work/H1-semantic/h1-preview-row-setter-composition/overnight-20261025-row-setter-composition/results-v4/report.json`.
The focused report assertion command is:

```powershell
python -m unittest tests.test_h1_preview_row_setter_composition_experiment
```
