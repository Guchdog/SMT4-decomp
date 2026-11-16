# Independent Post-Differential Review: `0x00286928` (`candidate_00286928`)

## Verdict

**Disposition:** **Accept** the static contract fidelity of `experiments/semantic_equivalence/h2_86928_candidate.cpp` (`SHA-256 a99dea239c82d4c132f2860581b204cfe48ad449caf927e1ee2aef6cb9b256af`) and the design of `tools/h2_86928_experiment.py` (`SHA-256 340f9c5ca81f41f48b5892b2cb73926304543466781dca617d716829792b29ae`) against the pinned `0x00286928` ARM body, **subject to** running `tools/h2_86928_experiment.py` under an allocated compiler slot (no cached `offline-report.json` was present at `build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix/run001/checks/default/offline-report.json` during this 0-slot read-only audit).

This review does not claim real-callee execution or live Azahar runtime equivalence.

## 1. Independent Disassembly of Pinned `0x00286928` (820 bytes)

Inspected `extracted/exefs/code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`) at `0x00286928..0x00286C5C`:

- **Raw selectors `11/12/13/14/15/19`, pointer selection, normalized selector, and `+0x2D`/`+0x5E`/`+0x5F` writes**:
  - `table = 0x0043E188`, `default_object = table[1]` (`r0`).
  - `11`: `object = table[2]`, `selector = 11`, `+0x2D = 0`, `+0x5E = 1`, `+0x5F = 1` (on `r2 == 0`).
  - `12`: `object = table[3]`, `selector = 12`, `+0x2D = 0`, `+0x5E = 0`, `+0x5F` untouched.
  - `13`: `object = table[2]`, `selector = 11`, `+0x2D = 1`, `+0x5E = 1`, `+0x5F = 1` (on `r2 == 0`).
  - `14`: `object = table[2]`, `selector = 11`, `+0x2D = 0`, `+0x5E = 0`, `+0x5F` untouched.
  - `15`: `object = table[2]`, `selector = 11`, `+0x2D = 1`, `+0x5E = 0`, `+0x5F` untouched (`0x286A38`: `r6=11, r2=1, r1=0`).
  - `19`: `object = table[2]`, `selector = 19`, `+0x2D = 0`, `+0x5E = 0`, `+0x5F` untouched.
  - All six match `h2_86928_candidate.cpp:25-44, 79-82`.
- **`incoming_r2` path families**:
  - `r2 != 0` (`0x2869BC..0x286A24`, `0x286B9C..0x286C4C`): handles `state == 4` (ret `1`), `state == 5` (`0x0028DF54(*(u32*)(object + 0x18))`, ret `1`), `state == 0` (`+0x2e == 0` gate on `selector in {11, 19}` + `default_object[8]`, or `+0x2e != 0` clear + `0x0028E974(..., 0x1a, 1, 0)` + conditional `0x0028DF98`), and other states (`0x002C1F28`, `0x002B89A0`, re-read `state`, `0x002B8D24`, `state = 3`, `+0x35 = 0`).
  - `r2 == 0` (`0x286A4C..0x286B98`): writes `+0x5f` if `flag != 0`, `+0x36 = (u8)arg5`, `*(u32*)(object + 0x10) = (selector == 6 ? 0x035ab9ff : 0x320202ff)`. When `object[8] != 0`, sets `+0x2e = 1`, calls `0x002B8D24(object, object[9])`, sets `object[8] = 3`, `+0x35 = 0`, returns `0`. When `object[8] == 0`, checks `0x002C1F28() != 0 && 0x002B89A0() != 0` (ret `1`), else calls `0x0028E974(..., arg6)`, conditional `0x002B787C`, conditional `0x0028DF98`, conditional `0x002C4BF0(p+4, 0x20)` + reload `p+4` + `0x002B90F0(p+4, 0x40)`, 6-iteration loop (`0x002F5B2C`, `0x002D65B4`), `row in 7..9 && 0x0028DF70(0) == 5` block, and `selector == 19 -> 0x002B8584(1)`.
- **`0x0028DF54` arguments & order**: Both `state == 5` (`0x286C40`) and `state == 0` (`0x286C18`) load the raw 32-bit word `*(u32*)(object + 0x18)` into `r0` before calling `0x0028DF54`, matching `h2_86928_candidate.cpp:50, 57`.

## 2. Candidate Relocations, Size, and Differential Harness Audit

- **Relocations**: All 17 unique callee symbols declared in `h2_86928_candidate.cpp:3-20` (accounting for the 22 call sites) resolve in `config/functions.csv` to even ARM addresses (`thumb=0`). `tools/h2_86928_experiment.py:75-111` validates `R_ARM_CALL` (`28`), checks `target & 1 == 0`, encodes `BL`, and rejects bodies `> 820` bytes (`SPAN = 820`).
- **296-case fixture & ABI comparison**: `directed_cases()` generates `23 * 2 * 6 + 2 * 5 * 2 = 296` cases, plus `3` `pointer_timing_cases()` and `5` `callback_cases`. `run()` compares `r0`, `SP`, `r4-r11`, `d8` (`FPEXC=0x40000000`), `events`, `writes`, full `OBJECTS`/`SERVICE`/`GLOBAL_OBJECT` memories, `fault`, `done`, `reads`, and `trace`. `8` compiled mutation controls test `mode_11`, `selector15_prewrite`, `selector19_pointer`, `r2_zero_state_call`, `df54_value`, `six_iteration_loop`, `unconditional_p4_read`, and `stale_pointer_after_2c4bf0`.
- **`0x00221168` composition**: **Yes**, `run(..., callback=True)` executes the original pinned `0x00221168` ARM body in Unicorn, stubs `0x00289640`, `0x0028686C`, and `0x00296F60`, and verifies `0x00221168 -> 0x00286928` ABI arguments `(0x12003456, 0x87654321, incoming_r2, 6)` and stack `(1, 0)`.

## 3. Missing Coverage & Limitations

- All 17 direct callees (`TARGETS`, including `0x002B8D24`) are stubbed in `tools/h2_86928_experiment.py`; no real callee bodies execute in this runner.
- `0x00221168` composition only exercises `selector=6`; the other 21 direct `BL` sites are not composed.
- `offline-report.json` was not present on disk in `build/agent-work/H2-semantic/h2-86928-q0-pointer-load-fix/run001/checks/default/` during this 0-slot review; a fresh run under a 1-slot assignment is needed to record compiled 812-byte size and live pass hashes.
