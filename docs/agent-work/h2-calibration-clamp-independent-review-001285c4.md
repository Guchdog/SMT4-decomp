# Independent review: `0x001285C4` calibration clamp

## Recommendation

**Accept the bounded clamp candidate for coordinator promotion review.** I independently audited the five signed-halfword clamp paths and reproduced the direct, mutation-control, and original-reader caller-composition evidence with a fresh output directory. The candidate is semantically supported for valid, disjoint ordinary RAM fixtures; byte identity and whole-title equivalence are not claimed.

## Independent source and contract audit

- Recomputed every declared `input_sha256` entry in the frozen reviewer `task.json`; all 14 matched. The pinned `code.bin` SHA-256 remains `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, and the implementation source remains `4a4e5240e44607caca4cf12387441bb17f243eb79e3e1343230a67569d411234`.
- Independently disassembled all 76 original bytes at `0x001285C4` as ARM. The five loads are signed halfword loads (`LDRSH`) from offsets `0`, `2`, `6`, `8`, and `0xA`; conditional halfword stores (`STRH{LT,GT}`) occur at those same offsets. Conditions are signed `< 40`, `< 36`, and `> 145` for the final three fields. Equality at each bound leaves the field untouched.
- The production C++ uses `s16*`, leaves calibration index 2 (relative offset 4) untouched, and applies the shared upper bound 145 to indices 3–5. The direct harness randomizes all halfwords and compares the entire 0x60-byte context plus ordered writes and registers, so unchanged bytes are included in the differential.
- The original reader call at `0x0011C61C` decodes to ARM `BL 0x001285C4` (`0xEB002FE8`). The target is even, so its bit 0 is clear and no ARM/Thumb transition is implied. Final-VMA staging also confirmed the entry remains at the original address.

## Fresh validation

All outputs are under `build/agent-work/H2-semantic/h2-calibration-clamp-review-001285c4/run001/checks/`.

- `python tools/h2_calibration_clamp_experiment.py --out build/agent-work/H2-semantic/h2-calibration-clamp-review-001285c4/run001/checks/reviewer-rerun-20261102` — exit 0. Fresh final-VMA run: 334/334 direct cases matched; 16/16 compositions through the original `0x001078D8` caller and original `0x0011C5EC` reader matched with the reader's controlled `0x0012A758` seam; all three negative controls were detected. Case set covers signed extremes and values below, at, and above each boundary.
- The fresh report confirms a 76-byte body for the 76-byte slot, zero candidate relocations, successful exact-slot IPS replay, and no staged image differences outside the original slot. The source differs from the original bytes (`byte_identical=false`); exact matching is not claimed.
- The script's affected implementation TU compile succeeded as part of that command. Separately compiled the consumer `src/engine/leaf_batch30_a.cpp` to the reviewer-private object path with `compile_tu_armv6k`; exit 0.
- All three negative controls were applied and detected: first minimum off by one, second clamp wrong field offset, and upper comparison changed from `>` to `>=`.

Fresh report SHA-256: `19fed01f71c4b97d602ef06ca036035bbd54cd856352644873d8a20f6c1ff63f`.

## Limits and next action

Evidence covers the clamp's direct behavior and its reader composition under valid, disjoint synthetic ordinary RAM, with a controlled ring-reader seam. It does not establish physical input provenance, ring producer freshness, scheduling, malformed-pointer or aliasing behavior, device/MMIO effects, natural runtime reachability, or whole-title `titleConfig` equivalence. Runtime/emulator verification was not run and is not required to decide this bounded offline review.

Coordinator can treat the independent review as passed and consider the candidate for promotion under the existing non-matching ledger policy. Integrated promotion still needs the coordinator-owned batch closure and the milestone's defined runtime scenario.
