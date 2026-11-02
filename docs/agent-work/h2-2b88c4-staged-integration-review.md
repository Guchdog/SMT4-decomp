# Independent review: staged `0x002B88C4` integration

## Decision

The staged artifact and pinned validation report support the bounded integration claim: the staged image differs from the reviewed run-013 base only within the `0x002B88C4` 220-byte slot; the IPS round-trips to that exact image; and the final ARM `BL` targets even ARM address `0x002BF6D0`. The validation runner actually loads the base and staged image bytes into Unicorn and executes the function at its final address for 58 matching cases.

This remains offline fixture evidence. The code path executes original `0x002BF6D0`, original byte-matching `0x002B0188`, and original `0x00138B90` from the mapped image, but the manager table, manager entry, touch work, node and optional rectangle are controlled memory fixtures. Runtime, natural scheduler reachability, real manager lifetime and full H2 behavior are not established.

## Frozen pins and patch scope

All 18 inputs declared by the run001 packet exist and match their pinned SHA-256 values. The pinned original `code.bin` identity is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The manifest pins the run-013 combined base image at SHA-256 `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291`, staged image at `62c922fc5f5c6049c511b8c4c0c1e0cb5754d1412908cdec0baa19b4da089dc0`, IPS at `4632b233d792ebb49aceb39c4820f45dcc57d81bc2c65cb0a77dd86a082c2344`, and manifest at `8dc9b27322b0ffd9f2a7028995df82935edb2096df5ccf7b99e2f140cea079e3`. The staged validation report SHA-256 is `06303cda68b5e86fb2be960a3e220f9ced6b74590aab2033ef33e97f3a9287f7`.

I independently opened the manifest's referenced base image and recomputed all of the base, staged and IPS hashes. Applying the IPS to the base produces the exact staged bytes. Byte comparison finds 200 changed bytes; all are between file offsets `0x1B88C4` and `0x1B89A0`, inside the declared 220-byte slot `[0x1B88C4,0x1B89A0)`. The full replacement record is 220 bytes: a 156-byte compiled body followed by 64 bytes of ARM NOP padding. The staged slot hash is the manifest replacement hash `c321bbaeb36d913f36121d8c0575b99bd2dfd25bfa3f7278b6f06a0f246b978f`. The base slot itself compares byte-for-byte equal to the pinned original `code.bin` slot, so this staged comparison isolates the changed function relative to that integration base.

The compiled body source SHA is `f47e857eeba6f823046feb42821b0a2d85eb7cdac4073b6e0e456fdfefc58eb0`; its manifest body hash `758376e357bbfc30f4dbcbdf0f7ac57f6df1483d9279908a9312889252076d60` is for the extracted pre-relocation ELF body. The replacement/staged slot contains the resolved branch. I decoded the staged instruction at function offset `0xC`: it is ARM `BL` `0xEB001B7E`, whose target is `0x002BF6D0` (even address). Its padding starts after byte 156 and consists entirely of `0xE320F000` ARM NOPs.

## Does the runner load the actual images?

Yes. `tools/h2_b88c4_staged_validation.py` reads `BASE` and `STAGED` from the manifest's concrete paths, recomputes both hashes against the manifest, and constructs two separate profiles via `experiment.setup(image=base)` and `experiment.setup(image=staged)`. `experiment.setup` maps the supplied image at virtual address `0x00100000`; both profiles then start at `0x002B88C4`. It is not merely installing a candidate body into the original `IMAGE` buffer.

The base and staged slots at `0x002BF6D0` compare equal to the pinned original 64-byte function span; their `0x00138B90` 36-byte body also compares equal to original. `0x002B0188` is byte-matching at final address as well. The staged path therefore executes the compiled touch-region C++ and the original resolver chain; no code hook substitutes those functions in this validation. Hooks record resolver arguments and writes. The fixtures still synthesize the table/global pointers and contents, manager entry/base, node data, optional rectangle, and writable touch-work region.

## 58-case validation and evidence boundary

The staged validator regenerates the 58 cases from the fixed counts `0, 1, 37, 199, 200` (both record forms) plus 48 seeded fixtures. For each, it compares observations from the base image and staged image: return, complete record bytes, count, ordered write trace, helper arguments, callee-saved registers, SP, completion and faults. The runner leaves the write hook's captured sequence unsorted, so ordered write equality is checked. The staged report marks all 58 cases passed and identifies the executing chain as staged `0x002B88C4`, original `0x002BF6D0`, original `0x00138B90`, with original byte-matching `0x002B0188`.

The staged validation report's `negative_controls` field references controls covered by the earlier pinned-original offline runner; this staged comparison itself does not re-run mutants. This distinction is recorded rather than treating the staged report as mutation evidence. Runtime is explicitly `not_run`.

## Recommendation

Accept the staged artifact as a slot-scoped offline integration with the stated fixtures. Keep ledger status `non_matching` for `0x002B88C4`; retain `matching` for final-address `0x002B0188`. Do not promote the result into a runtime/H2-equivalence claim: no Azahar execution, natural touch scheduler call path, real manager/table state or whole-scenario validation was performed. No build, staged-validation runner or emulator was run by this reviewer.
