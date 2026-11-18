# H18 family reconstruction: startup initializers `0x003F32F4..0x003F3428`

## Result

Reconstructed eight individual no-argument initializers from the ARM body inside the 800-byte `0x003F31D8` compound catalog span. Every entry is 0x2C bytes (nine instructions ending in `BX LR`, plus two literal words). The candidate implements two `-1` words and two zero words for each entry. The per-entry write addresses, literal pools, and behavior differences are in [the function-family record](../function-records/0x003f32f4-family.md).

The special case requested for `0x003F3320` is confirmed: its base literal is `0x00433E18`, but the `STRD` displacement is `+8`, so the `-1` values land at `0x00433E20` and `0x00433E24`; the zeros are written at `0x00433E28` and `0x00433E2C`. `0x003F3428` likewise uses a `+8` first-pair displacement.

## Validation

The focused tests pass and verify all eight `BX LR` boundaries, literal pools, four-word write maps, and the two `+8` cases. The seed-7 differential run passed 20 cases per entry and detected one negative control for each of the eight entries. Seed 20261024 passed 32 cases per entry; negative controls were not rerun for that seed. Both runs cycle all 16 input NZCV states and vary initialized RAM contents.

The first harness attempt caught a mistaken opcode offset in the validator. Disassembly showed STRD at `+0x0C`, not `+0x10`; after correcting that validator offset, all per-entry original/candidate comparisons passed. The corrected final report paths and hashes appear in the function-family record and handoff.

## Scope and caveats

No aligned direct `BL` or exact aligned pointer word to any entry was found in `code.bin`; invocation through startup registration remains unresolved. Differential evidence covers isolated initializer memory effects and ABI state in Unicorn. It does not establish caller composition, semantic names of the initialized globals, startup order, runtime behavior, or the full 800-byte compound span. No emulator or production ledger/source integration was performed.
