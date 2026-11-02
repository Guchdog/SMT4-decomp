# Independent review: in-place `0x0029F278` slot integration

## Recommendation

**Bounded approval for the in-place slot replacement and the tested offline comparisons.** I recomputed the prepared packet’s input hashes and independently ran the slot runner into fresh `run003` with seed `20261105` and 139 seeded samples. All 155 direct cases, all three original-image `TitleConfig_Calc` compositions, and all three accumulated-image compositions passed; the wrong-call-target negative control was detected. I found no counterexample within these fixtures. The conversion now fits in its original function span, so this removes the shared text-tail cave conflict for this helper. It does not establish runtime or whole-game equivalence.

## Provenance and rerun

All declared input hashes matched, including the base image, accumulated H2 image and manifest, run002 production/overlay files and report, candidate TU, runner, function record, contract, and integration note. Independent command:

```powershell
python tools/h2_29f278_slot_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-0029f278-slot/run003 --seed 20261105 --samples 139
```

Exit code: 0. The fresh report SHA-256 is `0949fa9d78b88f2a25215d41574d83671c572509f93db0fea0d7d4bf1941574c`; 155/155 passed, with no first counterexample. It pins original image `1f98884f…aa558`, accumulated base `acd8b2f3…51446`, source `545cf388…4481a`, object `92730352…7485f4`, replacement body `a31f235f…03ef8`, and slot IPS `e9922452…1ea5d8`. The new accumulated result is `d16516c9…1c9cb`, same as the prepared run002 overlay image.

## Slot, relocation, and overlay audit

The original span is 1536 bytes at `0x0029F278`; the candidate is 1024 bytes and its 4-byte `.rodata.cst4` table follows at `0x0029F678`. Combined size is 1028 bytes, leaving 508 bytes. The entry is even and word-aligned. The runner verifies fit, IPS roundtrip, and byte-for-byte suffix preservation. I independently compared run003 images: the accumulated base-to-overlay differences are all within the original function span; bytes after body plus table through the end of that span match the base; and the standalone production image contains the same body/table bytes while remaining equal to the pinned original everywhere else. The accumulated overlay hash matches the pinned run002 `code.h2-cursor.bin` hash.

The relocation report records 15 `R_ARM_CALL` entries to even ARM helper addresses: `0x002D5618`, `0x001FF3C4`, `0x002C615C` (twice), `0x002892C0` (twice), `0x002D5644`, `0x002BFFBC` (twice), `0x002C17D4` (four times), and `0x002BC200`. The sole `R_ARM_ABS32`, at body offset `0x3FC`, resolves to `0x0029F678` with bytes `08 04 01 02`. The word-aligned interior-entry census reports no external B/BL or aligned absolute-pointer candidates. Its stated limits remain: Thumb, computed/indirect branches and non-aligned pointer-like values are not detected. The exact 508-byte suffix is retained, and the IPS is independently applied to both base images by the runner with exact final-image roundtrip checks.

## Differential and caller results

The fresh run has 16 named boundary/control cases plus 139 seeded cases, all passing. It records no first counterexample and detects a wrong helper-call target. The direct comparison covers return/fault/stop state, PC, preserved `r4-r11` and SP, cursor and relevant input/global memory, helper call arguments/order, and ordered non-stack writes; restored stack scratch and incidental read multiplicity/order are excluded by the harness contract.

The three original-image state-1 caller cases passed: stable cursor, active cursor without input, and logical-bit cursor. The same three cases passed with the accumulated H2 base and the slot overlay. The caller harness executes the appropriate `TitleConfig_Calc` image and updater body; unrelated outer Calc service boundaries remain modeled. This demonstrates the six declared compositions, not arbitrary Calc states or natural user-input timing.

## Limits and next step

Fixtures use synthetic valid aligned ordinary RAM and controlled logical input state. Physical input delivery/scheduling, runtime sound, malformed pointers, concurrent access, MMIO aliasing, fault/read-order identity, and whole-game equivalence are unproven. The independent interior-entry scan is limited as described above. No emulator/runtime or full build was run in this review. The prior integration note reports the 204/204 build, but this review did not rerun it.

**Next action:** retain ledger status `non_matching`, accept the in-place slot patch for the integrator’s batch, and run the scoped accumulated-image runtime comparison when the offline-first gate and integration closure are complete.
