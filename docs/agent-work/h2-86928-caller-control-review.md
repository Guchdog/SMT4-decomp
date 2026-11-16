# Independent Caller & Control Review: `0x00286928` (`candidate_00286928`)

## Verdict

**Disposition:** **Accept** the recorded `run001/offline-report.json` (`02ce909c877cbdbeacf01efde7d7be4745c9e69526c5c18d23e182fa5f6e7385`) evidence for the 6 negative controls and `0x00221168` callback composition **for its recorded runner/source snapshot**, **with a provenance caveat**: `offline-report.json` pins an earlier `candidate_source_sha256` (`dc7a1cc9...`) and `runner_sha256` (`e41a2456...`), whereas HEAD `7e9db4d1` has updated `h2_86928_candidate.cpp` (`a99dea23...`) and `tools/h2_86928_experiment.py` (`340f9c5c...`, adding `pointer_timing_cases`, a 5th callback case, `production` parity, and 2 more controls).

This review does not claim original dependency behavior or live Azahar runtime equivalence.

## 1. Callback `0x00221168` Execution & Six-Argument Capture

Independently disassembled `0x00221168` in `extracted/exefs/code.bin` (`1f98884f...`) and audited `tools/h2_86928_experiment.py:164-278, 386-405`:

- **Pinned execution**: Both baseline and candidate runs start Unicorn at `0x00221168` using the pinned `IMAGE` bytes (with `0x00286928` patched only in the candidate/production runs).
- **Callback setup & 6-arg capture**: `0x00221168` calls `0x0028DF3C(0)`, `0x00289640()` (if `0`, writes `table[2]+0x30 = 1`, `table[2]+0x31 = 1`), sets `table[1]+0xa11 = 0x14`, calls `0x0028686C()` (`r7`), `0x00296F60(0)` (`r6`), `0x00289640()` (`r2`), pushes `[sp]=1, [sp+4]=0`, and calls `0x00286928` with `r0..r3 = (0x12003456, 0x87654321, incoming_r2, 6)`. `on_code` captures both `r0..r3` and `[sp], [sp+4]` at `0x00286928` entry (`helper[1] == expected`, `helper[2] == (1, 0)`).
- **Return & visible writes**: `run()` compares `r0`, `SP`, `r4-r11`, `d8`, `events`, `writes` (`UC_HOOK_MEM_WRITE`), `OBJECTS[0..2]`, `SERVICE`, `GLOBAL_OBJECT`, `fault`, and `done`.

## 2. Six Named Mutations, 300 Comparisons, Slot Padding & Relocations

In `build/agent-work/H2-semantic/h2-helper-00286928-convert/run001/offline-report.json`:

- **Six mutations**: `mode_11`, `selector15_prewrite`, `selector19_pointer`, `r2_zero_state_call`, `df54_value`, and `six_iteration_loop` are all `true`. `tools/h2_86928_experiment.py:443-444` explicitly asserts `mutant_body != body` before running each path-specific control against the pinned original.
- **300 comparisons**: `direct_cases: 296` + `real_callback_compositions: 4` = `300` total comparisons (`340`? Note: HEAD `tools/h2_86928_experiment.py` expands this to `296 + 3 + 5 = 304` with `8` controls).
- **Slot padding & relocations**: `compiled_body_bytes: 812`, `slot_bytes: 820`, `nop_tail_bytes: 8` (`2` ARM NOPs `0xE320F000`). All `22` relocations are `type: 28` (`R_ARM_CALL`), all targeting even ARM addresses (`target_state: "ARM"`, verified in `config/functions.csv`).

## 3. Fixture/Stub Limits & Next Action

- `0x00289640`, `0x0028686C`, `0x00296F60`, and all `17` direct callees of `0x00286928` (`TARGETS`, including `0x002B8D24`) are deterministic stubs; `0x00221168` only exercises `selector = 6` (21 other direct `BL` sites remain uncomposed).
- **Next action**: Run `python tools/h2_86928_experiment.py` under a 1-slot assignment to refresh `offline-report.json` against HEAD `7e9db4d1` (`h2_86928_candidate.cpp` `a99dea23...`, `leaf_batch45_a.cpp`, `h2_86928_experiment.py` `340f9c5c...`).
