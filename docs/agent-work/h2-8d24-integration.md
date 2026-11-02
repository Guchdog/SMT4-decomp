# `0x002B8D24` production integration and validation

## Integrated replacement

`battle_func_002b8d24` is now typed C++ in `src/engine/leaf_batch46_a.cpp`; the ledger row is `non_matching`. The production TU object contains a 356-byte body with no relocations, byte-identical to the reviewed candidate. `tools/h2_8d24_staged_image_patch.py` compiles the actual production TU, checks the 360-byte slot, validates direct helper call addresses are even ARM addresses, pads the last four bytes with ARM NOP, emits an IPS and verifies round-trip. Standalone image SHA-256 `36f3f5c03f45fb9bfb121d5803401ec5bab734fdda3fcb3b1981885de358c45a`; IPS SHA-256 `35aac4d1dc6d2744e8163ec10a5319eea63ffecefae81c6e38e9654b8d77c125`.

## Checks

- `python tools/build_check.py --tu src/engine/leaf_batch46_a.cpp --out-dir build/h2-8d24-integration/tu -j 1` — exit 0.
- `python tools/build_check.py --repo-root . --out-dir build/h2-8d24-integration/full-build -j 8` — exit 0; 204/204 TUs.
- `python tools/h2_8d24_experiment.py` — exit 0; 116 direct cases, two selector-11 compositions through original `0x00286928`, two five-call selector-12 alias chains, seven negative controls. Output SHA-256 `7c7873a9c74d907cea2f042955a0213bb8a1fb1ce5d5153cdd603e615b8ca8ce`.
- `python tools/h2_8d24_staged_validation.py build/h2-8d24-integration/staged-image/code.h2-8d24.bin` — exit 0; 116 direct and two caller cases against the staged production image.
- The same staged validator passed on the cumulative image below; bytes outside the declared slot equal the base composition.
- The independent selector-12 review is [h2-8d24-case12-alias-review.md](h2-8d24-case12-alias-review.md). It found the chain valid and recommends proceeding; see also the [independent implementation review](h2-8d24-review.md).

## Paired H2 runtime

Autonomous local-GDB Azahar comparison: [runtime report](h2-8d24-runtime.md). The exact cumulative final image is `build/h2-8d24-integration/runtime-image/code.h2-runtime.bin`, SHA-256 `f87b3149c03a58cc16eb3e903f0102b6f7ce47fdb3523740e992c3824f94e940`; original-based IPS SHA-256 `53f5da5aa13cdb6acfa2aa22ab3a8315fb103affb94cbbfc56f127b3019fbbc7`. It layers this conversion onto the previously reviewed final H2 image and passes IPS replay. Runtime matched 51 scripted actions and 19/19 checkpoints. The verifier did not instrument `0x002B8D24`, so a hit at this helper is unverified; the result is cumulative-image parity for the scripted path, not function-specific execution evidence. The report explicitly leaves full H2 acceptance false because readiness and same-session re-entry did not complete on either side, and physical input mapping/scheduling remain unproven. The earlier H2 composition report records source snapshot mismatches for some mapper/FillPair TUs; the runtime claim is scoped to these exact image bytes.
