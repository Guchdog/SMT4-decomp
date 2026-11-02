# Independent production review: `0x0029F278` updater

## Recommendation

**Bounded approval for the standalone production candidate and its current offline evidence.** I independently rebuilt and ran the frozen production runner into a fresh output with seed `20261103` and 137 seeded samples. It passed 153/153 direct original-versus-patched cases, all three `TitleConfig_Calc` compositions, and detected the wrong-target negative control. I found no counterexample in the stated fixture domain. This supports retaining the candidate as a production-classified `non_matching` reconstruction and proceeding to an integrator-owned closure; it does not support accumulated-image placement or runtime/whole-game claims.

## Provenance and independent rerun

Every SHA-256 in the prepared run001 packet matched before execution, including the pinned image, candidate TU, production runner, dependency runner, run006 inputs and function record. The rerun used:

```powershell
python tools/h2_29f278_production_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-0029f278-production-review/run007 --seed 20261103 --samples 137
```

Exit code: 0. Fresh report: 153 cases passed, no first counterexample, wrong-target control detected. The report pins the same source (`545cf388…4481a`), object (`92730352…7485f4`), original image (`1f98884f…aa558`), patched image (`bb1e15d0…27c36`) and IPS (`9933b58a…32fea`) as run006. The new compiled body remains 1024 bytes with SHA-256 `8816683a…101e4`; the report itself is copied into this packet’s `reports/` directory for handoff validation.

## Patch and relocation audit

The runner compiles only the assigned production TU and rejects any unexpected relocation census. The report contains 15 `R_ARM_CALL` relocations, all targeting even ARM addresses in the pinned original image: `0x002D5618`, `0x001FF3C4`, `0x002C615C` (two sites), `0x002892C0` (two), `0x002D5644`, `0x002BFFBC` (two), `0x002C17D4` (four), and `0x002BC200`. Its sole local absolute relocation is at body offset `0x3FC`, targeting `.rodata.cst4` at `0x003FEA24`; the four bytes are `08 04 01 02`. With cave start `0x003FE624` and the exact 1024-byte body, the table is placed immediately after the body. The production builder verifies the entire `0x9DC` cave is zero-filled in the pinned image and that body plus table fits.

The entry patch bytes `e9 7c 05 ea` encode an unconditional ARM branch from `0x0029F278` to even address `0x003FE624`. The IPS is reapplied and compared byte-for-byte with the built final image. The original function suffix after the first four-byte entry branch through the 1536-byte span is preserved. The runner’s interior-entry census found no external word-aligned ARM B/BL or aligned absolute-pointer candidates into the original body. This census does not cover Thumb, computed/indirect branches, or unaligned pointer representations; the report labels that limit. No observed direct interior target or relocation issue remains in the audited scope.

## Differential and caller evidence

All 153 direct comparisons passed: 16 named cases plus 137 seeded cases. Named cases cover the disabled short circuit, stable/no movement, first and second axes, both axes, threshold boundary, width-one and divide-zero-width fixtures, zero/nonzero remainder, wrap and total-position boundaries, high-bit signed position, bitset/logical queries, and query-counter paths. Comparisons include stop/fault/PC, r0, preserved r4-r11/SP, full cursor bytes, input globals/state/counts, helper call order/arguments, and ordered non-stack writes. The control that changes the branch target to `0x003FE628` is detected.

All three original `TitleConfig_Calc` state-1 compositions passed: stable cursor, active cursor without input, and logical-bit cursor. The harness runs the actual updater from each respective image and lets its direct divide helper execute from that image; it retains `CalcMachine`’s modeled outer service boundaries. These establish the listed synthetic caller scenarios, not every real caller state or physical input route.

The candidate/source and ledger are consistent: `config/functions.csv` classifies `0x0029F278` as `non_matching`, and the source declares the divide dependency as `u64`, consuming quotient in r0 and remainder in r1. This is a stateful 1536-byte wrapper with 15 original helper calls, so promotion remains contingent on integrating its dependencies and defining runtime scenarios coherently.

## Limits and next action

Inputs are synthetic valid aligned ordinary RAM; helper bodies remain pinned originals. Physical input semantics/scheduling, real sound delivery, malformed pointers, concurrent access, MMIO aliasing, incidental restored-stack scratch and discarded read/fault order are outside the comparisons. The three caller runs retain modeled outer service boundaries. The standalone patch occupies the text-tail cave and is not merged with the cumulative H2 image, which currently has a cave-allocation conflict. No emulator, runtime profile, accumulated image, full build or whole-game equivalence was tested. The static interior census has the coverage limits noted above.

**Next action:** integrator-owned batch closure should resolve the shared cave placement and composed-image dependencies, then validate the defined original-versus-patched H2 scenario. Keep the ledger label `non_matching`; do not promote the standalone pass to runtime equivalence.
