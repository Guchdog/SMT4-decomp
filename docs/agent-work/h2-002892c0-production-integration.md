# H2 `0x002892C0` production integration — run003

## Result

The production C++ symbol `camp_func_002892c0` builds as a 136-byte relocation-free ARM body. It does not fit the 124-byte original slot, so the builder retains the following function and places the helper at the reviewed executable text-tail VMA `0x003FEE64`. It writes an unconditional ARM `B` at the original entry `0x002892C0`; the encoded target is aligned, even, in range, and preserves LR. A 412-byte zero-filled cave range was available in the Calc-only base.

The builder reconstructs the Calc-only H2 base from the pinned image, then adds the helper entry and body. Its combined four-record IPS reapplies to the measured image exactly. The offline final-address differential passes 1,220 direct helper cases and 360 compositions through the original `0x0029EDFC` wrapper. The Calc-only base separately passes 68 cases. A control redirecting the helper entry to candidate address +4 is detected.

| Evidence | Result |
| --- | ---: |
| Pinned source image SHA-256 | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Calc-only base SHA-256 | `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d` |
| Combined image SHA-256 | `1d994ed8667ba97c084719d7ecf61934e005e938bdd22c7d160207c9953f4355` |
| Combined IPS SHA-256 | `1419cbfe64feda2062879f1ad14316a6fc7e71704cdab8c78fbe252d8ad100c3` |
| Production source SHA-256 | `584582c0a9f7831ec985a5ef62c36ca44141c778168dbe256abc72545359402d` |
| Production object SHA-256 | `8685537de0589910b26a0b695b50607a791220e5f9e0a277b57a2a8e89ef97ae` |
| Helper body SHA-256 / size | `32ed9c8c6ad393ddc586da13a9b667115f3847f4928fb0cd54aadf9718f964fc` / 136 bytes |
| Helper direct / wrapper cases | 1,220 / 360 |
| Negative control | detected |
| Runtime | not run |

Reproduce with `python tools/h2_2892c0_production_integration.py --out-dir build/agent-work/H2-semantic/h2-titleconfig-002892c0-integration/<new-run>`. The runner freezes the production source hash, rejects a reused output directory, rebuilds and validates the Calc-only base, compiles the production TU, audits the cave and ARM branch encoding, constructs the combined IPS, and compares original and patched images at final guest addresses.

## Scope and limits

The comparison baseline is the independently validated Calc-only H2 image. The modified image adds only the `0x002892C0` helper replacement. Direct tests compare object bytes, ordered writes, return, helper-entry arguments, completion, SP and `r4-r11`; wrapper fixtures test the original `0x0029EDFC`, including disabled skip behavior.

The accumulated five-callback H2 patch uses the shared text tail for Calc, Draw, and Secondary. This helper body is not merged into that full image because its cave range is already allocated there. `0x0029F278` itself is still original and was not run as a caller. This run does not establish physical input or sound behavior, scheduling, invalid pointer behavior, concurrent or MMIO semantics, persistence, Azahar runtime, or whole-game equivalence. The exact scope and recovered semantics are recorded in [the function record](../function-records/0x002892c0.md).


Independent review reproduced the patch builder into a distinct output directory, matched the combined image and IPS hashes, replayed the IPS, checked the cave and ARM entry branch, and accepted the helper on this Calc-only base. The independent review and handoff are in [h2-002892c0-production-independent-review.md](h2-002892c0-production-independent-review.md). The full ARMv6K build passed 204/204 translation units. The review retains the cave-collision and untested-caller limits above.