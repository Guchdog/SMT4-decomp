# H2 composed final image and offline validation

## Result

Composed the reviewed Thumb-corrected five-callback image, three production
configuration mappers, and `UiConfig_FillPair` into one IPS against the pinned
original. `UiConfig_CopyPair` at `0x002ADB40` (20 bytes) is unchanged. The final
`code.bin` image is **3,633,152 bytes**, SHA-256
`acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`; its IPS
SHA-256 is `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`.
The image differs from the original in 4,218 bytes, all within the reviewed
callback IPS records, the three 92-byte mapper slots, or the 24-byte FillPair
slot. The complete image hash, IPS hash, incremental input identities, patch
record hashes, and IPS replay are in the run manifest.

The immutable composition is under
`build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/`.
Offline results are under `checks/offline-001/`.
The final manifest SHA-256 is
`577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`; the
aggregated offline report SHA-256 is
`0ecd97778086ecee46df70af1b12d3ec5a5d2f023bb8962d451b90d96b92dfea`.

## Offline checks

All image-level differential suites used the exact composed image above:

| Family | Result | Negative control |
|---|---:|---|
| Draw | 46/46 | Detected helper call shifted by four bytes |
| Calc | 16/16 sequences | Detected incorrect logical mapping |
| Secondary | 34/34 | Detected wrong loop-count control |
| Initializer | 10/10 | Detected wrong sprite-group count |
| Ready gate | 4/4 | Detected always-ready control |
| Three config mappers | 512/512 each | Wrong-map control detected for `0x002CAB70` |
| FillPair | 4,096/4,096 | Wrong high-byte mask detected as data-memory difference |
| State 9/10 caller composition | 3/3 | Wrong Calc callback address detected |

The secondary, initializer, mapper, and FillPair negative controls were read
from already existing task artifacts; this task did not build those objects.
Mapper suites compare original entry points to the candidate code at the
corresponding entry points in the final image. The caller harness used matched
HLE boundaries and executed against the same final image and manifest.

## Provenance and execution caveats

The mapper and FillPair production **object** hashes match their accepted
manifests. Their current working-tree source files do not match the source
hashes recorded when those objects were produced:

- Mapper TU B: expected `dd9dac02bd19c27dd0fdfc9897229757bfc71f68a3e7fb4532ac781c873f325c`,
  current `882993acbf47d181b3881cec61d26731ebc3a72737eee804f6b7a897cbde710e`.
- Mapper TU C: expected `9baf88cee24f0b53c2d330171c194d5795132907b77db0396cc29842fe3743de`,
  current `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa`.
- FillPair TU: expected `b5e511d0bae599ac38a13b6df68918444c00aece51ebcb760e0817897c18adf8`,
  current `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2`.

The reviewed objects and image payloads remain reproducible from the pinned
artifact hashes, but this checkout cannot establish that the current source
files are the exact source snapshots that produced them. No source was edited.

One workflow deviation occurred: invoking
`h2_offline_caller_composition.py --final-initializer` still compiled its
initializer-caller object. It completed successfully into this task's private
`checks/offline-001/caller/` output, with compiler exit 0. This exceeded the
packet's zero-compiler allocation. No canonical build cache was used, and no
further compile or rerun was performed after discovering the behavior. The
caller report records that build. The standalone compositor and its Python
tests do not compile anything.

This is bounded offline ARM differential and caller evidence. HLE boundaries
remain as described by the underlying reports. No Azahar launch, profile,
debugger, network, UI automation, save-persistence, or visible-menu behavior
was exercised. Do not treat this composed image as runtime or whole-game
equivalence evidence.

## Commands and outcomes

Successful commands:

```text
python tools/h2_final_image_compose.py --output build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003
python -m unittest tests.test_h2_final_image_compose
python tools/h2_final_image_compose.py --validate-image build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/code.h2-final.bin --manifest build/agent-work/H2-semantic/h2-final-image-composition/run-001/composed-003/manifest.json --output build/agent-work/H2-semantic/h2-final-image-composition/run-001/checks/offline-001
```

The test suite passed 3/3. The offline command exited 0 and wrote the individual
callback, mapper, FillPair, and caller reports. Its caller subprocess compiled
the initializer-caller object as noted above. Two earlier composition attempts
failed before producing a deliverable: the first correctly surfaced mapper
source drift, and the second exposed a FillPair manifest-key assumption; both
were corrected before `composed-003`.

## Recommendation and next action

The composed image is ready for independent artifact/provenance review and
isolated runtime evaluation only after the coordinator resolves the recorded
source-snapshot mismatch and accepts the zero-compiler deviation. Retain the
no-savestate/no-persistence claim. Runtime comparison remains `not_run`.
