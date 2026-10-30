# Review: H2 live final-image pins

## Disposition

**Accept the pin update for this review scope.** The live preflight constants identify the reviewed composed H2 image, IPS, integration manifest, and current private observer executable. Package provenance includes the live preflight, its test, and the wrapper module. Static review found no stale image or private-binary pin and no missing negative identity/path control in the supplied tests.

## Independent hash checks

The twelve packet read-path hashes matched the run-001 snapshot. The private delivery manifest verified all 29 entries (feature inputs, compatibility inputs, patches, and executable). The three composition artifacts also matched their authoritative identities:

- Final composed image, `code.h2-final.bin`: `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`.
- Standalone IPS, `code.h2-final.ips`: `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`.
- Composition/integration manifest: `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`.
- Current private `azahar.exe`, matched by delivery-manifest `binary.sha256` and `EXPECTED_PRIVATE_AZAHAR_SHA256`: `e9eaa321899a796c17e9460cf8b4a7e003e2606712f1fcc8f1fb485d8f5f406d`.
- Original H2 image remains pinned as `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The live preflight constants for the staged CCI (`9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`) and staged Azahar (`c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`) match the prior final-image pin review. The actual staged CCI and staged executable were not rehashed in this review because their paths are not declared in this packet; the conclusion here is that the source pins remain intact and agree with the recorded review, not fresh staged-file hash evidence.

`package_h2_delivery.py` includes `h2_live_preflight.py`, `test_h2_live_preflight.py`, and `h2_azahar_launch.py` in `feature_inputs`; their current hashes match the manifest. The package binary hash also matches the live preflight pin.

## Source and fixture review

- Live preflight checks the staging-root manifest identity and containment; validates the pinned original/final image, IPS and integration-manifest hash/content; checks the CCI hash and SMT4 program ID; checks staged executable identity for both profiles; and validates separate profile roots and disabled GDB/RPC settings.
- Private executable resolution accepts only normalized relative manifest paths beneath the delivery root. It rejects absolute, traversal, drive-qualified, UNC, malformed and wrong-root paths, checks the manifest/delivery root and each existing path component for reparse points, and confirms resolved containment and file identity. The output path is restricted to a fresh direct `.jsonl` child of the stage root and rejects traversal and reparse cases.
- The focused test file defines pre-subprocess rejection controls for wrong private binary, integration manifest, final image, and IPS. It also covers CCI hash/title rejection, path variants, wrong-root binary, ancestor reparse simulation, output traversal/reparse, profile mismatch, and live/movie conflict.
- The valid live command assertion requires `--h2-live`, excludes `--movie-play`, checks the selected staged profile and working directory, and requires CCI as the final argument. A separate regression assertion checks the CTM route still contains `--movie-play` and excludes `--h2-live`.

These are source and test-assertion findings only. This review did not run tests, build or stage files, launch the wrapper/Azahar, or access profiles. It establishes pin consistency and guard coverage; it does not establish runtime behavior or H2 equivalence.

## Next action

The coordinator may accept the pin-update review. Keep staged-artifact hash verification and any manually controlled live runtime comparison in their separately assigned scope.
