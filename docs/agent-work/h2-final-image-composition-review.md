# Independent review: composed H2 production image and IPS

## Recommendation

**Accept the bounded offline image composition and recommend it as the exact artifact for the next isolated runtime stage.** The composed image and original-based IPS are internally reproducible, the mapper and FillPair source drift is resolved at the selected function-body level, and the final image contains all four selected production bodies. This review does not accept interactive H2 behavior or close the H2 milestone; the differential suites are bounded offline evidence with explicit HLEs and no Azahar run.

## Artifact identity, overlay path, and write scope

The task packet pins the extracted original `code.bin` SHA-256 to `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Every input hash in the corrected run-003 packet matched. The final composition manifest and its ten referenced inputs also matched their recorded hashes. The output is 3,633,152 bytes:

- Final image: `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`
- Original-based IPS: `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`
- Manifest: `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`

I independently replayed all 533 final IPS records in memory against the pinned original. Each record's offset, length, and payload hash matched the manifest; the replay was byte-identical to the saved final image. The final image differs from the original in 4,218 bytes, and every differing byte falls within a declared final IPS record. CopyPair (`0x002ADB40`, 20 bytes) remains byte-identical to the original.

The component-image relationship is an overlay composition, not serial replay of the three component IPS files. The composer first verifies the pinned callback, mapper, and FillPair image hashes. It copies the callback image, copies three 92-byte mapper replacement slots from the pinned mapper image, then copies the 24-byte FillPair body from the FillPair manifest after confirming it appears in the pinned FillPair image. It authorizes only those mapper/FillPair slots in addition to the callback manifest's ranges, rejects any changed byte outside that union, preserves CopyPair, and encodes a fresh IPS against the original. I independently reconstructed this exact overlay: the result matched the final image, and the 212 bytes changed relative to the callback image were all inside the three mapper slots and FillPair slot. This explains why a mapper extension IPS cannot be treated as an incremental IPS against the Thumb-corrected callback image: its own pinned base/image lineage differs. The exact final IPS is original-based and is the artifact suitable for staging.

The callback base itself is pinned as `cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4`; mapper and FillPair source images are pinned as `97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c` and `5e9aa08b449985f012e24400c45b4b037e4a0d5d069723b6cfa7ccf83300d8fa`. Their image, IPS, and manifest input hashes match the composition manifest. The composed IPS record set has 533 entries and 4,218 changed bytes. This is a non-identical production image; no byte-matching claim is made.

## Source, object, and selected-body identity

All nine object identity entries in the composition manifest match their pinned SHA-256 values. Five whole source-file identities match. Four whole source-file hashes differ from their earlier accepted-source pins: mapper A (`src/engine/leaf_batch32_b.cpp`), mapper B/C (`src/engine/leaf_batch32_c.cpp`), and FillPair (`src/engine/leaf_matching.cpp`). I independently rehashed the current files and confirmed the current-source audit records those same hashes.

The selected-function audit resolves this at the requested body level: all four selected bodies and relocation lists compare equal to their accepted object extraction. I also hashed each body at its final image slot (`file offset = VMA - 0x00100000`); each image slot matches both the current-source and accepted body hashes:

| Function | Final image body SHA-256 | Bytes |
|---|---|---:|
| `0x0021F39C` mapper | `616fdaa08187217f5859996444b65cdce852f6b045f047e0497df4602eaa0451` | 48 |
| `0x002CAB70` mapper | `fbb5b34c4b5b94322cb10ba9da7257fa4010d82c3aa6f754e54d6b32a14c2438` | 48 |
| `0x002E0AF4` mapper | `8b99e056165e42868b91ef1d6498d392261d3fd37197b6ac42331d75ea2e5aaa` | 48 |
| `0x0027EDF8` FillPair | `43f1278d7a4e61088c5b91786351f36a1d949a0d00294e3e617d7813c9bb648c` | 24 |

The mapper replacement spans are 92 bytes each, including padding; the selected executable bodies are 48 bytes. The FillPair span/body is 24 bytes. The report should retain the whole-source drift as provenance context; it should not say that the older whole translation units produced the current objects. The selected compiled body is the identity established here.

## Same-image differential evidence

The aggregate offline report binds to the final image hash and composition manifest hash. Its same-image suites report:

- Draw: 46/46, with the helper-call-plus-four negative control detected.
- Calc: 16/16 persistent sequences (54 ticks per seed in the paired seed runs), with a wrong-logical-map control detected.
- Secondary: 34/34, with its changed helper-argument/order control detected.
- Initializer: 10/10, with a wrong-sprite-group/work control detected.
- Ready gate: 4/4, with an always-ready control detected.
- Each of the three mappers: 512/512. The aggregate per-mapper report marks a wrong-map control detected for `0x002CAB70`; it does not mark separate controls detected for the other two entries.
- FillPair: 4,096/4,096 over byte inputs, four high-bit patterns and destination offsets 0–3; wrong high-byte mask control detected.
- State-9/10 initializer caller composition: 3/3; wrong primary Calc callback address control detected. The trace observes the expected FillPair call at `0x0027EDF8` with `r0=0x0200201C` and `r1=0xFFFFFFFF` on both sides.

No first counterexample is recorded in these bounded reports. The composition report states `runtime: not_run`. Its caller command compiled one task-local object and exited 0 despite a zero compiler allocation; the producer documented this workflow deviation. I did not rerun it or compile anything. This is an execution-budget deviation, not an image hash or differential mismatch, and should remain disclosed in the provenance record.

## Contract and runtime limits

This evidence supports only the declared contracts and exercised offline cases. Mapper inputs are zero-extended bytes (`0..255`). FillPair covers eight writable bytes of ordinary target memory at destination residues 0–3; it does not prove fault/MMIO/concurrency behavior or every caller's allocation lifetime/alignment. Callback and State-9/10 harnesses retain matched HLEs for allocation, task/process services, sprite/resource/cursor setup, touch registration and physical input, sound, reset/transition, environment/model services, and related runtime behavior. The caller composition compares registration/linkage and the selected readiness path but does not schedule Calc, Draw, or Secondary. These reports do not establish actual input mapping/cadence, UI appearance, edit/cancel/confirm behavior, guest/save bytes, persistence, restart, Azahar runtime behavior, or whole-game equivalence.

The correct next action is to stage only this reviewed final image/IPS for the separately assigned, isolated original-versus-patched runtime comparison, after the integrator verifies CTM action coverage and profile isolation. Keep H2 open until the required runtime records and remaining criteria are reviewed.

## Review method

Read-only review. I read the task packet, repository workflow instructions, composition tool, manifests, linked reports, and prior integration reviews. Python inspection scripts rehashed packet inputs, artifact pins, source/object identities, selected bodies, image/IPS records, and overlay reconstruction; the final IPS parser applied records in memory. All completed verification commands exited 0 except one initial inspection script that assumed every manifest entry had a single `path` field and exited 1 on a callback-object `paths` array; I corrected that script and verified all declared source/object pins. No files were changed during inspection, and no build, test, emulator, profile, debugger, network, or input automation was used.
