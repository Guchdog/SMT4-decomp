# Independent review: `0x00254CA8` logical query and axis gate

## Recommendation

**Bounded approval only when the axis reader writes both output floats.** I verified the frozen inputs and ran the harness into fresh run007 with seed `20261113` and 53 seeded samples. The run passed all 89 comparable direct cases out of 90 total, all three H2 original-mover compositions, and the wrong-helper-target control. The no-write axis-reader fixture is explicitly excluded (`pass: null`) even though the observed original and candidate happen to compare equal. Nothing establishes that live H2 avoids that domain, so this is not approval for unrestricted promotion.

## Provenance and artifact

All packet `input_sha256` values matched before the rerun. Command:

```powershell
python tools/h2_254ca8_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-00254ca8-offline-integration/run007 --seed 20261113 --samples 53
```

Exit code: 0. The report SHA-256 is `6b53e5063f2375559b11157169fc0a027f6dbc2e8968a38e58b9962b376f4d69`. It records a 640-byte candidate body (`9a77100a…997786`), source `b24453a8…1d15b5`, object `2c5715a9…49145f`, original image `1f98884f…aa558`, and slot IPS `db232574…3400ae`. I verified the IPS reapplies to the pinned original image to produce the reported final image (`51d9abbd…60697e`), that no bytes outside the 640-byte body changed, and that the original suffix of 200 bytes in the 840-byte slot is unchanged. The relocation census is 18 ARM call relocations: 12 to `0x002C17D4`, two each to `0x002BFFBC` and `0x002B902C`, one to `0x0027FBC8`, and one to `0x002820A4`; all are even pinned ARM addresses.

## Ordering, selector, and calibration audit

The pinned ARM contract and C++ body agree on mode behavior:

- Mode 0 calls `0x002BFFBC(id0)` then `id1`, ORing the results.
- Mode 1 calls `0x002B902C(id0)` then `id1` unconditionally, calls `0x002C17D4(id0)`, and calls its `id1` form only if the first mask query is nonzero. Only when both mask queries are nonzero is the second mode-1 result suppressed.
- Mode 2 calls the two mask queries in ID order and ORs them. Unsupported modes leave the base result zero but still reach shared special-ID logic.

The special selector prefers a special `id0` (12–15) over a special `id1`. A zero availability byte at `0x00465288` returns the base result. Otherwise the first ordered trigger scan checks IDs 14, 15, 12, 13 and short-circuits on success; the axis helper then receives two local output pointers and mode 0. The C++ intentionally leaves `x`/`y` uninitialized and does not default them. It reads them after the call without using the returned status, matching the explicit candidate domain only when both outputs are written.

After finite VFP angle conversion and the negative-angle `+360` adjustment, all-zero written samples return the base result before a second ordered 14/15/12/13 query scan. The successful second scan selects signed halfword pairs `(0,1)`, `(2,3)`, `(4,5)`, or `(6,7)` in the calibration block. The ID14 condition includes the extra angle-bit-pattern comparison against 360 before endpoint checks. ID13 uses a negated `>` comparison for its second boundary. Selector suppression clears only the selected base result. The direct cases cover first/second selector precedence, availability, trigger order/rounds, all four sectors and finite angle/calibration boundaries; I found no mismatch in the inspected code or report.

## FPSCR and comparison boundaries

Both original and candidate direct executions explicitly start with `FPSCR = 0` and `FPEXC = 0x40000000`; `SP` is set to the same fixture value. Post-call FPSCR is recorded, but removed from the equality comparison because its condition/status flags are caller-saved. Fresh run007 reports 42 FPSCR differences among the 89 comparable cases. This is visible diagnostic evidence under a normalized initial FPSCR; it does not establish behavior for inherited/unusual FPSCR state or NaN/Inf VFP conditions. The runner compares SP and its captured callee-saved subset (r4-r8 and d8); it does not capture r9-r11, which the pinned contract says are not modified by this body.

For the explicitly excluded `special-no-write-reader-excluded` case, the original reader returns without writing the output slots and the candidate then reads indeterminate local floats. The report correctly assigns this row `pass: null`, not a pass or failure; `equal_incidentally: true` is not semantic evidence. The implementation has no defined portable behavior here. Neither the static setup nor current H2 compositions prove this path unreachable. Do not silently expand the approved domain or initialize outputs to zero without a separate contract decision.

## H2 original-mover compositions

All three controlled compositions through the pinned original `0x001FF3C4` mover passed: initialized idle, primary ID 6 with ID 15 axis path, and primary ID 6 with ID 14 axis path. These execute the patched query service in the image and compare the original service image; query/counter/mask, axis-reader output values, and angle results are supplied deterministically by the harness. The fixtures write both axis output floats and use H2 initialized IDs. They corroborate these composed offline branches, not live service cadence or natural input scheduling.

## Limits and next action

Physical controls, live axis-reader status/output validity, natural H2 no-write reachability, runtime sound/input timing, NaN/Inf and unusual FPSCR behavior, exact read/fault order, concurrency/MMIO, and whole-game equivalence remain unresolved. No full build or emulator was run in this review. The ledger remains `non_matching`.

**Next action:** retain the explicitly bounded written-output domain, seek caller/runtime evidence for no-write reachability before widening the claim, and let the integrator decide whether that unresolved path blocks production use.
