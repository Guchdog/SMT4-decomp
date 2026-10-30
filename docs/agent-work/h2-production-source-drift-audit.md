# H2 production-source drift audit

## Result

Rebuilt the three current production TUs in distinct task-private output
directories, one compiler job each. Extracted the three mapper symbols and
`camp_func_0027edf8` from current objects and their accepted objects. Every
selected body is byte-identical to its accepted counterpart and all four
relocation maps are equal and empty. The changed TU C object therefore reflects
changes outside the two audited mapper bodies. Source hashes differ from the
accepted manifests, but the selected implementations did not change.

This audit did not read the composed image or its manifest. Current body hashes
for independent image-slot verification:

| Symbol | Address | Size | Current body SHA-256 | Accepted body SHA-256 | Equal |
|---|---:|---:|---|---|---|
| `camp_func_0021f39c` | `0x0021F39C` | 48 | `616fdaa08187217f5859996444b65cdce852f6b045f047e0497df4602eaa0451` | same | yes |
| `camp_func_002cab70` | `0x002CAB70` | 48 | `fbb5b34c4b5b94322cb10ba9da7257fa4010d82c3aa6f754e54d6b32a14c2438` | same | yes |
| `camp_func_002e0af4` | `0x002E0AF4` | 48 | `8b99e056165e42868b91ef1d6498d392261d3fd37197b6ac42331d75ea2e5aaa` | same | yes |
| `camp_func_0027edf8` | `0x0027EDF8` | 24 | `43f1278d7a4e61088c5b91786351f36a1d949a0d00294e3e617d7813c9bb648c` | same | yes |

The SHA-256 of the extracted comparison report is
`56b2fbca4206fc0f4893a076f5f02ec53a1252ec46e452fcd456cb7db926f833`.
It contains the exact current and accepted object hashes, source hashes, body
hex, body hashes, and relocation records.

## Source and object identities

| TU | Current source SHA-256 | Current object SHA-256 | Accepted object SHA-256 | Finding |
|---|---|---|---|---|
| `leaf_batch32_b.cpp` | `882993acbf47d181b3881cec61d26731ebc3a72737eee804f6b7a897cbde710e` | `2aea8bc429a521f894546bd550b44b53d8940493d10d880b06dc188c588d772d` | same | Entire rebuilt object matches; selected mapper is identical. |
| `leaf_batch32_c.cpp` | `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa` | `681e67ee676c636d756e50f668101913ce344d7626b0efc31c9bd4888315e164` | `5d0f079cfc288754d3035e0aa2484b88b5e04dcac6e95073efa9280d5931c58d` | TU object differs, but both selected mapper symbols match. |
| `leaf_matching.cpp` | `90238ffc67607cdb8578d1ce65aa6370389deb527423d3b0b278e43f6f621da2` | `b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3` | same | Entire rebuilt object matches; FillPair is identical. |

Thus the tracked source drift does not alter any of the four promoted
implementations. TU C's different whole-object hash is localized outside the
selected bodies by the exact per-symbol extraction. The audit does not claim
that every unselected function in TU C is semantically unchanged.

## Build and comparison commands

All three builds exited 0 under `tools/build_check.py`, each using `--jobs 1`
and a separate output path:

```text
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch32_b.cpp --out-dir build/agent-work/H2-semantic/h2-production-source-drift-audit/run-001/current-tu-b --jobs 1 --force
python tools/build_check.py --repo-root . --tu src/engine/leaf_batch32_c.cpp --out-dir build/agent-work/H2-semantic/h2-production-source-drift-audit/run-001/current-tu-c --jobs 1 --force
python tools/build_check.py --repo-root . --tu src/engine/leaf_matching.cpp --out-dir build/agent-work/H2-semantic/h2-production-source-drift-audit/run-001/current-tu-fill --jobs 1 --force
python build/agent-work/H2-semantic/h2-production-source-drift-audit/run-001/compare_selected.py
```

The first comparison invocation exited 1 because its private script did not add
the repository root to `sys.path`; that import path was fixed and the same
command then exited 0. No production source, image, accepted object, or
manifest was modified. No emulator or runtime validation was performed.

## Limits and next action

The current and accepted ARM object bodies prove exact identity for these four
selected functions, but do not prove whole-game behavior, caller execution,
runtime behavior, or equivalence of other functions in changed translation
units. The coordinator/image reviewer can independently check the supplied
body hashes against image slots without using this worker to inspect the image.
