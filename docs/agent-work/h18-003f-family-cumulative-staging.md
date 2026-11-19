# H18 cumulative staging: reviewed `0x003f` initializer entries

## Result and image chain

Composed the 11 reviewed initializer bodies onto the existing integrated H18 image, without changing production source or board files. The frozen original-to-H18 chain passed independently: applying `code.h18-final.ips` to pinned original `code.bin` reproduces H18 base SHA-256 `efdb59e33463e964dbb1d9884a92d23dc8e4e4f78390c4e7810414f956a03d12`; the original and base are both 3,633,152 bytes. The H18 base IPS has 2,335 records, and none overlaps any of the 11 complete target slot intervals.

Before composition, every target slot was required to match original byte for byte. All 11 did. The final body placements are `0x003f3274` (120/128 bytes), eight 36/44-byte bodies from `0x003f32f4` through `0x003f3428`, and `0x003f34a0`/`0x003f34cc` (36/44 bytes each). The compiler helpers reject unresolved relocations; each final entry is ARM-word aligned.

## Artifacts and preservation

Fresh outputs are under `build/agent-work/batch-h18-001/h18-003f-family-cumulative-staging/run-001/checks/cumulative-final/`:

- Cumulative image `code.h18-family-final.bin`: SHA-256 `ba4149f1ba302e8acb22782d89435d8fe6e38d0ebec0ca63b3a50dc72b56545e`.
- Overlay IPS (H18 base → cumulative image) `code.h18-family-overlay.ips`: `d94d484cbb1e087e74e07eb845b772e5f98730ac568a34c2254b963fa7dc519c`.
- Combined IPS (pinned original → cumulative image) `code.h18-family-combined.ips`: `645a02e44712d734293ce16641e22b6fca0783b14170cb3f99dfe48e5793a026`.
- Report: `report.json`, SHA-256 `826403cf9cda73aa2bfac8ad6ac5000e21893e68804a952754d6a73e21f651d7`.

Reapplying both the overlay IPS to H18 base and the combined IPS to original yields the exact cumulative image. There are 361 changed bytes relative to H18 base, all confined to the 11 candidate bodies. The H2 text cave `[0x003fe624,0x003ff000)` remains byte-identical to H18 base (SHA-256 `f12e73ba462e4a6acb3a1c65504c5aeca69606eb3d1c07d2b4b6a774ea98dc16`); the oversized original `[0x003f3454,0x003f34a0)` remains identical too. Every other preexisting H18 byte was preserved.

## Final-address checks

The extracted final-image bodies passed 20 directed differential cases each at their final ARM VMAs: 20 for `0x003f3274`, 20 for each of the eight-entry `0x003f32f4` family, and 20 each for `0x003f34a0` and `0x003f34cc` (220 total). All 15 negative controls were detected (5 + 8 + 2). The excluded `0x003f3454` was executed from both H18 base and cumulative images in 20 cases; the traces matched and the original ARM-to-Thumb transition was observed each time.

The assigned utility and tests are `tools/h18_003f_family_cumulative_staging.py` and `tests/test_h18_003f_family_cumulative_staging.py`. The unit suite checks IPS composition, exact slot membership, target-byte drift rejection, overlapping H18 patch-record rejection, candidate overflow, cave preservation, and `0x003f3454` preservation. Syntax compilation and all four unit tests passed.

## Evidence limits and next action

These offline Unicorn checks use synthetic fixtures. They do not establish an actual startup caller or initialization order. The `0x003f3454` iterator path remains modeled by its existing runner. The cumulative image is a private staging artifact, not a production ledger/source promotion or whole-game-equivalence result. A separate caller/startup investigation and independent review of this exact cumulative image/IPS are the next steps before promotion consideration.
