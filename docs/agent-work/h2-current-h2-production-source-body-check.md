# H2 production source-to-image body audit

## Result

The three current production TUs compiled successfully with the repository ARMv6K Clang 23.1.3 configuration into private task output (one compiler at a time). All four selected function bodies are relocation-free and byte-for-byte equal to both their previously accepted object symbol and the exact bytes at their function slots in the composed H2 image `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`.

| Function | Body SHA-256 / size | Current TU SHA-256 | Fresh object SHA-256 | Previous object SHA-256 | Exact image-body match |
|---|---|---|---|---|---|
| `0x21f39c` | `616fdaa08187217f5859996444b65cdce852f6b045f047e0497df4602eaa0451` (48 B) | `882993acbf47d181b3881cec61d26731ebc3a72737eee804f6b7a897cbde710e` | `2aea8bc429a521f894546bd550b44b53d8940493d10d880b06dc188c588d772d` | `2aea8bc429a521f894546bd550b44b53d8940493d10d880b06dc188c588d772d` | true |
| `0x2cab70` | `fbb5b34c4b5b94322cb10ba9da7257fa4010d82c3aa6f754e54d6b32a14c2438` (48 B) | `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa` | `681e67ee676c636d756e50f668101913ce344d7626b0efc31c9bd4888315e164` | `5d0f079cfc288754d3035e0aa2484b88b5e04dcac6e95073efa9280d5931c58d` | true |
| `0x2e0af4` | `8b99e056165e42868b91ef1d6498d392261d3fd37197b6ac42331d75ea2e5aaa` (48 B) | `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa` | `681e67ee676c636d756e50f668101913ce344d7626b0efc31c9bd4888315e164` | `5d0f079cfc288754d3035e0aa2484b88b5e04dcac6e95073efa9280d5931c58d` | true |
| `camp_func_0027edf8` | `43f1278d7a4e61088c5b91786351f36a1d949a0d00294e3e617d7813c9bb648c` (24 B) | `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2` | `b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3` | `b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3` | true |

This resolves the concern that the manifest's whole-TU `source_identity_mismatches` imply a different selected H2 mapper or FillPair body. The warning remains valid at whole-file granularity: notably the fresh `leaf_batch32_c.o` differs from the previous full object, but its two selected mapper symbols are identical to the old objects and image. This report does not certify unrelated symbols in those TUs, change any image or ledger entry, or alter the existing experimental/non-matching classifications.

Current source versus manifest source hashes:

- `src/engine/leaf_batch32_b.cpp`: current TU `882993acbf47d181b3881cec61d26731ebc3a72737eee804f6b7a897cbde710e`; manifest expected `dd9dac02bd19c27dd0fdfc9897229757bfc71f68a3e7fb4532ac781c873f325c`; whole-TU hash matches: `False`. Selected body still matches previous object and final image.
- `src/engine/leaf_batch32_c.cpp`: current TU `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa`; manifest expected `9baf88cee24f0b53c2d330171c194d5795132907b77db0396cc29842fe3743de`; whole-TU hash matches: `False`. Selected body still matches previous object and final image.
- `src/engine/leaf_batch32_c.cpp`: current TU `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa`; manifest expected `9baf88cee24f0b53c2d330171c194d5795132907b77db0396cc29842fe3743de`; whole-TU hash matches: `False`. Selected body still matches previous object and final image.
- `src/engine/leaf_matching.cpp`: current TU `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2`; manifest expected `b5e511d0bae599ac38a13b6df68918444c00aece51ebcb760e0817897c18adf8`; whole-TU hash matches: `False`. Selected body still matches previous object and final image.

## Prior semantic evidence applies to these bytes

The existing mapper integration report covers all byte-valued inputs under two seeds, and FillPair covers destination alignments 0–3 and low-byte patterns; both have negative controls. Their caller/final-image evidence is recorded in the copied integration/composition reports under this run's `reports/`. Because this audit establishes the exact selected symbol bytes in the final composed image, those offline results apply to the same body bytes. This is still bounded ARM/offline evidence, not a new runtime test.

## Commands and scope

The three fresh TU builds and function extractor ran with private outputs; each exited 0. Compiler flags and sidecar dependency hashes are preserved with the `.o.json` files. `python tools/agent_workflow.py check` also exited 0. No source, final image, ledger, profile or save was modified, and no emulator was launched.

The H2 acceptance gap is not source/body lineage for these four functions. H2 remains open for full runtime input/action evidence: the paired CLI run recorded matching state snapshots but no logical query input/return events, and its exact loaded executable identity is not reconciled to the delivery manifest. The candidate image and whole-game behavior remain unpromoted/unproven.
