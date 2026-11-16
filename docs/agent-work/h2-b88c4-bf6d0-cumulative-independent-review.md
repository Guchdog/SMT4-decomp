# Independent review: cumulative H2 touch-region image (`0x002B88C4` + `0x002BF6D0`)

## Result

**Verdict: Bounded Acceptance (`ready_for_review`)** for the cumulative two-slot H2 touch-region composition (`camp_func_002b88c4` at `0x002B88C4` and `camp_func_002bf6d0` at `0x002BF6D0`) staged onto the reviewed `run-013` base image (`code.combined.bin`).

All 14 frozen `input_sha256` pins from `task.json` were verified intact. Independent recompilation and two-slot staging into private output (`run-001/fresh-staging`) reproduced the exact staged image (`e643173a604c331e6b333086d7df227ec9a684baa92e91b476851b433d1bb369`) and two-slot IPS patch (`1204c568d38245efbb93bb7e12252019a27a8e7156fb574948f71204a1a6e280`). Fresh original-caller differential runs against the `run-013` base image passed `58/58` cases with `0` mismatches under distinct seeds (`20261120` and `20261131`). This supports bounded offline composition acceptance only; live Azahar runtime was not run in this task.

## Artifact, Slot-Extent, Fill, Relocation, and Interworking Audit

- **Pinned Original Image (`extracted/exefs/code.bin`)**: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` (`3,633,152` bytes).
- **Reviewed `run-013` Base Image (`build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin`)**: `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291` (`3,633,152` bytes).
- **Two-Slot Staged Image (`code.h2-touch-region-bf6d0.bin`)**: `e643173a604c331e6b333086d7df227ec9a684baa92e91b476851b433d1bb369` (`3,633,152` bytes; identical across `run001/staging`, `run-001/staging`, and independent recompilation in `run-001/fresh-staging`).
- **Two-Slot IPS Patch (`code.h2-touch-region-bf6d0.ips`)**: `1204c568d38245efbb93bb7e12252019a27a8e7156fb574948f71204a1a6e280` (`302` bytes: `PATCH` header, two records at file offsets `0x1B88C4` (`220` bytes) and `0x1BF6D0` (`64` bytes), and `EOF` trailer). Applying the IPS to the `run-013` base image round-trips byte-for-byte to the staged image (`ips_roundtrip = true`).
- **Manifests**:
  - `build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging/manifest.json`: `57ece72cf0a00310a630f02d39508c5ab072d218d15c408ffc3ff7c3e52102bf`
  - `build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run-001/staging/manifest.json`: `e093fe639466c442a915a5f9edd9c87a17b6284cb96eb41f579255a3b0d00bfc`
  - `build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration-review/run-001/fresh-staging/manifest.json`: `aee4ed052bed3302253eecefdbf83ec38052a4fcd814a3c61331091f561d79c9`
- **Slot 1 — `camp_func_002b88c4` (`0x002B88C4..0x002B89A0`, file offset `0x1B88C4..0x1B89A0`, span `220` bytes)**:
  - Compiled body: `156` bytes (`acb5aae8d45c8d7ac0131786c07639a6a70d56b75f35af8734a72a9f8cac8932`).
  - Slot fill: `64` trailing bytes (`16` ARM NOP words `0xE320F000`) at `0x002B8960..0x002B89A0`; full `220`-byte replacement SHA-256 `c321bbaeb36d913f36121d8c0575b99bd2dfd25bfa3f7278b6f06a0f246b978f` (`200/220` bytes differ from `run-013` base).
  - Relocation & interworking: 1 `R_ARM_CALL` at offset `+12` (`0x002B88D0`), instruction word `0xEB001B7E`, decoding to `0x002B88D0 + 8 + (0x1B7E << 2) = 0x002BF6D0` (`target_bit0 == 0`, even ARM entry of staged `camp_func_002bf6d0`).
- **Slot 2 — `camp_func_002bf6d0` (`0x002BF6D0..0x002BF710`, file offset `0x1BF6D0..0x1BF710`, span `64` bytes)**:
  - Compiled body: `60` bytes (`e025ae963514db7c95f9cb2193a02758cb55a4b6bb34f45bb7bbd00b5aee7162`).
  - Slot fill: `4` trailing bytes (`1` ARM NOP word `0xE320F000`) at `0x002BF70C..0x002BF710`; full `64`-byte replacement SHA-256 `cbba2af9a3811c3db9906dc0b88074fa308292067d29702601a2741cc639ecf2` (`42/64` bytes differ from `run-013` base).
  - Relocations & interworking:
    1. `R_ARM_CALL` at offset `+8` (`0x002BF6D8`), instruction word `0xEBFFC2AA`, decoding to `0x002BF6D8 + 8 + (-0x3D56 << 2) = 0x002B0188` (`target_bit0 == 0`, even ARM entry of `ui_func_002b0188`).
    2. `R_ARM_CALL` at offset `+28` (`0x002BF6EC`), instruction word `0xEB001A9A`, decoding to `0x002BF6EC + 8 + (0x1A9A << 2) = 0x002C615C` (`target_bit0 == 0`, even ARM entry of `ui_func_002c615c`).
- **Whole-Image Footprint**: Across all `3,633,152` bytes, exactly `242` bytes (`200 + 42`) differ between `run-013` base and the staged image, and `0` bytes differ outside the two declared spans (`only_declared_slots_changed = true`).

## Fresh Caller Comparison (`0x002B88C4 -> 0x002BF6D0 -> 0x002B0188 / 0x002C615C`)

Commands executed:

```powershell
python tools/h2_b88c4_bf6d0_staged_image.py --output build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration-review/run-001/fresh-staging
python tools/h2_b88c4_bf6d0_staged_validation.py --base build/agent-work/H2-semantic/h2-init-ready-final-image/run-013/combined-build-final/code.combined.bin --staged build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging/code.h2-touch-region-bf6d0.bin --manifest build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration/run001/staging/manifest.json --out build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration-review/run-001/checks/caller-seed-20261131 --seed 20261131
```

- **Exit codes**: `0` and `0`.
- **Fresh validation reports**:
  - `build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration-review/run-001/checks/caller-seed-20261131/report.json` (SHA-256 `9b5d1c66b3ef3c81bad29892e1361fafeb7bef6de2a6f39100e332cd0ff9d2ec`, `seed = 20261131`, `58/58` passed, `mismatches = []`).
  - Prior review seed run: `build/agent-work/H2-semantic/h2-touch-region-manager-current-resolver-integration-review/run001/checks/review-seed-20261120/report.json` (SHA-256 `b3f4e3b906e8c12a649eceb498cc72b722d467ab4085e4ea7f53b2143195b386`, `seed = 20261120`, `58/58` passed, `mismatches = []`).
- **Verified behavior across all 58 cases**:
  - **Count boundaries**: Directed counts `0`, `1`, `37`, `199`, and `200` (each tested with `custom = False` and `custom = True`), plus `48` seeded cases (`count in 0..199`). For `count in 0..199`, returns old `count` and updates `TOUCH_WORK + 0x64A` to `count + 1`; for `count == 200` (full capacity), returns `0xFFFFFFFF` (`-1`), leaves `count == 200`, and performs `0` non-stack writes.
  - **Both record forms**: Verified both `custom = True` (non-null rectangle pointer at `node + 0x0C`, copying `node + 8/+0x0A` and `rect + 0/+2`) and `custom = False` (null pointer at `node + 0x0C`, copying `node + 8/+0x0A` and `node + 4/+6` with bit 15 masked via `& 0x7FFFu`), plus preservation of all surrounding bytes in the `0x640`-byte record array (`TOUCH_WORK + 0x0A..0x649`).
  - **Argument traces**: Both `caller_args` at `0x002BF6D0` and `manager_args` at `0x002B0188` matched `((0x1D, 0x572),)` on every case.
  - **Ordered non-stack writes**: For every in-capacity case (`count < 200`), both `run-013` base and the two-slot staged image emitted the exact same 5 ordered 16-bit stores: four ascending halfword stores to `TOUCH_WORK + count*8 + 0x0A..0x10` followed by the incremented count store to `TOUCH_WORK + 0x64A`.
  - **Stack-residue exclusion & ABI state**: Temporary call-frame writes below `SP` (`[STACK - 0x100, STACK)`, i.e. `0x00A0FE00..0x00A0FF00`, where the called original divider `0x002C615C` and call frames spill registers) are excluded from `external_writes`, while restored `SP == 0x00A0FF00`, `r4–r11`, `done == True`, and `fault == None` are strictly verified.

## Limits

- The fixtures provide valid, aligned, controlled manager (`0x00901000`), manager table (`0x00940000`), indirect table (`0x00900100`), node (`0x00910000 + 20*r`), rectangle (`0x00930000`), and `IfTouchWork` (`0x00920000`) ordinary-RAM data for `(group=0x1D, node_id=0x572)`.
- Writes in `[STACK - 0x100, STACK)` are excluded to tolerate temporary call-frame/divider spill bytes below `SP`; equality of dead stack residue below `SP` is not claimed.
- Runtime scheduler reachability, manager lifetime, physical touch input behavior, concurrency/atomicity, malformed-pointer fault behavior, and whole-title runtime equivalence remain untested in this offline review.
- Both `0x002B88C4` (`156/220` bytes) and `0x002BF6D0` (`60/64` bytes) remain `non_matching` in the byte ledger.
