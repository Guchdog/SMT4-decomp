# Group #19: four-word record writers

## Result

Status: `probada_arm` for the recorded four-word RAM contract only. The three
original functions have identical 36-byte ARM bodies. A normal C++ candidate
for each compiles to 20 bytes and passes bounded differential execution against
the original ARM at both gates under two seeds. This is not a byte match, caller
runtime validation, or proof of whole-game equivalence. Production definitions
and the matching ledger are unchanged.

The candidate is in
[`aoc_initializer_candidates.cpp`](aoc_initializer_candidates.cpp), and the
underlying single-seed harness is
[`aoc_initializer_experiment.py`](../../tools/aoc_initializer_experiment.py).
The two-seed entry point added for this family is
[`group19_four_word_record_experiment.py`](../../tools/group19_four_word_record_experiment.py).

## Inspected contract

Arguments are ordinary ARM AAPCS words: `r0` destination, `r1` source pointer
value, `r2` buffer pointer value, and `r3` size. The destination must be a valid,
four-byte-aligned 16-byte RAM record. The function writes:

| Offset | Value |
|---|---|
| `+0x00` | incoming `r1` |
| `+0x04` | zero |
| `+0x08` | incoming `r2` |
| `+0x0C` | incoming `r3` |

It returns the original destination in `r0`; its callee-saved registers and
stack are restored by the original body. The source and buffer are stored as
opaque values and are not dereferenced. Any 32-bit size value is accepted by
the leaf itself. Null destination, misalignment, inaccessible destination,
overlap with MMIO, concurrency, and downstream resource validity are outside
the tested domain. The input pointer values may equal one another or alias the
destination's word addresses; they are snapshotted in argument registers before
the stores.

The disassembly at each address is the same nine-instruction sequence:
save `{r4,r5,r6,lr}`, preserve `r2/r3`, store `r1` at `+0`, store `r3` at
`+0xC`, store zero and saved `r2` at `+4/+8`, then restore. The writer's store
order differs from the C++ candidate's order, but these are ordinary RAM stores;
the final destination image and the runner's tracked observable access
footprint match. The original also saves callee registers in scratch stack space
below entry `sp`, which the runner intentionally does not classify as live
stack; removing that scratch save/restore is allowed for this leaf as long as
`sp`, callee-saved registers, and live caller stack remain unchanged. This claim
does not extend to device memory or concurrent observers.

## Caller evidence

Callers below were checked manually in `tools/split_asm.py` output and pinned
instruction-by-instruction by the harness. They are static evidence only; no
caller window was executed differentially in this experiment.

- `0x003530F8` is called at `0x0038B424` from
  `aocApplication_func_0038b384`: `r1 = [r4+0x80]`, `r2 = [r4+0x5AC]`,
  `r3 = 0x20000`; the returned pointer is stored at `[r4+0x5A8]`.
- `0x00352950` is called at `0x0038B5B0` from
  `aocApplication_func_0038b510`: `r1 = [r4+0x80]`, `r2 = [r4+0x5B4]`,
  `r3 = 0x20000`; the returned pointer is stored at `[r4+0x5B0]`.
- `0x00354D28` is called at `0x0038DEBC` inside
  `script_vm_func_0038de60`: the destination is `sp+0x8D0`, source is
  `[r4+0x80]`, buffer is `sp+8`, and size is `0x400`. The next call at
  `0x0038DED4` passes this record to `0x00354C30`. The exact semantic type name
  for this VM descriptor is not established.

These facts establish argument setup and observed uses, not the full ownership
or downstream lifetime contract of either resource type.

## Differential evidence

The runner verified the pinned game image SHA-256 before execution and checked
the nine original instructions and each caller snippet. Both seeds ran 12 fixed
cases plus 1,024 seeded cases per function. All three candidates passed all
2,072 cases each (1,036 per seed), and every negative control was detected as
`data memory differs` by changing the reserved word from zero to one.

| Address | Original bytes | Candidate bytes | Cases per seed | Result |
|---|---:|---:|---:|---|
| `0x00352950` | 36 | 20 | 1,036 | pass, both seeds |
| `0x003530F8` | 36 | 20 | 1,036 | pass, both seeds |
| `0x00354D28` | 36 | 20 | 1,036 | pass, both seeds |

Pinned image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
Original body SHA-256 (all three):
`6353e01e8c71da9542d40c7007e88cfdd33534957e97143a24dd05f84b672c1b`.
Candidate source SHA-256:
`69c4537a8ebad556184f4a3b66582f868d8fbbb0bd1eec9204a1389094b762c8`.
ARM compiler: `clang version 23.1.3` (MSYS2 package revision
`067886dba977a6b4c97dfedfb25286b5eda55620`). The harness uses the project's
`compile_tu_armv6k` toolchain settings. The experiment output also records the
object hash and per-case results in ignored `build/` artifacts.

Reproduce from the authorized worktree, using the same private `code.bin` for
the pinned game revision:

```powershell
python -m unittest tests.test_group19_four_word_record_experiment tests.test_aoc_initializer_experiment -v
python tools/group19_four_word_record_experiment.py --code extracted/exefs/code.bin --output build/semantic-equivalence/group19-records-run-20261024 --seeds 20261024 7 --samples 1024
```

The recorded run summary is at
`build/semantic-equivalence/group19-records-run-20261024/group19_summary.json`
(ignored; not committed). The focused test run passed 7 tests. Test seed runs
use 4 random samples per seed to keep the unit test quick; the standalone
reproduction command above is the 1,024-sample run.

## Limits and next evidence

This is isolated ARM-vs-C++ execution under the project's bounded RAM runner.
It does not validate real callers, loader behavior, live game execution, resource
ownership, or hardware/MMIO ordering. Seeds and boundaries are broad evidence,
not a proof for all memory models. Exact byte matching remains false for all
three candidates. Before treating them as integrated reconstructions, build
caller windows with equivalent observations and verify their behavior against
the original; for a runtime claim, show that the patched game actually enters
each function under corresponding original/patch scenarios.
