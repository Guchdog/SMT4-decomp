# H2 private Azahar live-package review

## Decision

**accept** the packaged artifact provenance and patch scope for this bounded review. The delivery manifest pins Azahar source revision `219d743a1e698101fe1ab8bef43e6563126c3c27`; its current executable hash matches the manifest at `88562997988d50ae11551b727212dfd3d853b1de5cf4bd67a94aec22dc7f5495`. All manifest-declared feature inputs (16), compatibility inputs (6), and patches (4) hash-match their current package files. The feature patch contains the reviewed live logical-query return capture and Ctrl+Shift+F8 on-demand snapshot path.

This is a provenance/source-scope review only. It does not verify that the executable starts, that it was built from exactly these inputs by a reproducible build, or that runtime behavior matches the source review.

## Package identities

| Artifact | SHA-256 |
|---|---|
| `h2-delivery-manifest.json` | `a154e1d2b8b566cd2b33ca274d0e23b95f57c34bfd6df0ba42e490e9657e7b7c` |
| `azahar-h2-observer.patch` | `9d148f78e72034ec0457da8d384da871bfafaaccf8f65fa36c71d9e7a557ea09` |
| `build-clang64/bin/Release/azahar.exe` | `88562997988d50ae11551b727212dfd3d853b1de5cf4bd67a94aec22dc7f5495` |
| `h2_azahar_launch.py` | `6e3b66d49652807b71e9db5dcd28e2aa7aa022226a51e02f8a1398c89f86acbb` |
| `package_h2_delivery.py` | `d6b49a0a129819d3f91cfd1e825ce6c2241bb6d86c3ec56e7c28a85a975613f6` |

Manifest patch hashes also matched: `build-compat-shims.patch` `66b6f37a5a93f1037508ad6b50f05949fdd5ef924e7a8ff766e82ddfa9a3a25b`, `build-compat-dynarmic.patch` `d94dde4a720e295eec708b627fd05ca9c10fdf0415759cc3c75364b4d09ed815`, and `build-compat-libressl.patch` `2dbf1b273213f60416a5579fb094b87adb0e92a07a2b84d74d4b3c5a893947db`. The manifest’s compatibility checkout heads match current HEADs: dynarmic `e77b1ba0b7da7cbe93021b01a663acfe7c4dd516`, libressl `88b8e41b71099fabc57813bc06d8bc1aba050a19`.

Every one of the 16 `feature_inputs` and 6 `compat_shim_inputs` entries in the manifest was independently SHA-256 checked against its current package file; all matched. The Azahar checkout HEAD equals the manifest’s `base_commit`. The package generator declares the feature file allowlist and emits feature and compatibility patches separately.

## Patch scope and launch route

The generated feature patch has exactly these ten source paths, all from the generator’s feature allowlist: `src/citra_cli/citra_cli.cpp`, `src/citra_qt/bootmanager.cpp`, `src/citra_qt/citra_qt.cpp`, `src/core/CMakeLists.txt`, `src/core/core.cpp`, `src/core/core.h`, `src/core/movie.cpp`, `src/core/movie.h`, `src/core/h2_observer.cpp`, and `src/core/h2_observer.h`. It contains `--h2-live` configuration and rejects combining live mode with movie playback or a pad start index. It also wires `logical_query_return` records and the Ctrl+Shift+F8 shortcut to `RequestH2ManualSnapshot`; it contains no unrelated file paths. The four build-compatibility patches are separately listed in the manifest and are not part of the feature patch.

The reviewed `h2_azahar_launch.py` validates the supplied private executable against the delivery manifest's expected path and SHA-256, runs the capture preflight for the selected `original` or `patched` profile, and constructs a CTM movie-play command with `--h2-snapshot`, run-root, user-dir and start-pad arguments. It does **not** pass `--h2-live`; the source explicitly disallows live mode with movie playback. Therefore the wrapper remains the guarded replay/capture route and does not provide a live-input launch route. The live mode is present in the packaged feature patch/binary provenance, but must be invoked through an independently guarded manual launch setup. The earlier source review records the preflight's profile-pair checks; this review did not inspect profile contents or execute that preflight.

## Evidence and limits

- Compiled/build: `not_run` by this reviewer. The manifest pins a binary hash but cannot by itself prove its build inputs or behavior.
- Differential/caller: `not_run`.
- Runtime: `not_run`; no executable, wrapper, profile, emulator, debugger, RPC/network route, or input automation was used.
- Hash verification and source/patch scope review: completed read-only. The manifest and patch are private package evidence, not a runtime equivalence result.

Next action: coordinator may accept the package provenance and assign any separate guarded runtime comparison. If live mode is to be part of a supported wrapper workflow, add and independently review a dedicated safe live-mode launch route; the existing wrapper is intentionally movie-replay-only.
