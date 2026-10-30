# H2 final-image staging tool update

## Result

Updated the isolated profile stager to accept `--expected-manifest-sha256`. When omitted, the tool still enforces the original pinned run-004 manifest hash `4002ab29da801d36eafd17fd728d0473f50d7d10ec6c786ba3135b6b431140cf`. Passing an explicit hash lets the integrator opt into another reviewed image/manifest pair, including the composed H2 image. The supplied image hash, pinned original, CCI, Azahar executable, profile seed file allow-list, output-root restriction, portable debug/RPC settings, standalone IPS generation and replay, and profile-difference checks remain enforced.

Manifest record validation now checks each record's structure, bounds, and payload hash, requires records in offset order, and merges touching/overlapping intervals as they are read. The changed-byte scan advances one interval cursor over the image. With ordered records this is O(record count + image bytes), replacing the prior O(record count × image bytes) membership scan. The 533-record final-composition manifest satisfies the ordering and coverage contract.

## Focused fixture tests

Added tests for default-hash resolution (including the unchanged run-004 pin), a custom manifest hash accepted against a temporary manifest fixture, wrong-hash rejection, declared versus undeclared changed-byte coverage, and a 1,024-record ordered fixture. The temporary custom fixtures only exercise manifest/coverage helpers; the existing stage guards continue to use temporary directories. No real CCI, profile seed, or Azahar executable was staged.

Command: `python -m unittest tests.test_h2_manual_final_image_stage`

Result: **10 tests passed**, exit 0. An initial run exposed a validation-order regression in an existing test: the new helper read the original before rejecting an incorrect manifest. The stager was adjusted to preserve the previous manifest-before-original rejection order; the final 10-test run passed.

Command: `python tools/h2_manual_final_image_stage.py --help`

Result: exit 0; usage shows `--expected-manifest-sha256` and describes its default as the reviewed run-004 pin.

I also applied the new interval-coverage helper read-only to the pinned original, composed H2 image, and its manifest. All 533 declared records passed payload/bounds/order validation, and every changed byte was covered; exit 0.

No profile stage, Azahar launch, debugger, network operation, or input automation was performed. This tool update prepares the exact reviewed composed image for the separately authorized staging task; it supplies no runtime evidence.

## File identities

Task-pinned input hashes matched before editing. Final modified-file hashes:

- `tools/h2_manual_final_image_stage.py`: `7c3c0a1506537061960e58b48f6e111689d65cd523c9a605a2af05e6adca7f77`
- `tests/test_h2_manual_final_image_stage.py`: `4aa98bc62a5898a293b07138183f06dda04b8fa180c2a77c835eacc09b491c0a`

The selected custom manifest for the composed final image has SHA-256 `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`; the caller must pass it explicitly with the reviewed composed image. The old default manifest remains unchanged.
