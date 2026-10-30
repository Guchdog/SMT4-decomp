# H2 fresh paired stage with shared pinned CCI

## Result

Created fresh original and patched portable profiles at
`E:\SMT4decomp\build\h2-manual-comparison\run-012` for the reviewed composed
H2 image. This image contains the five title callbacks plus the three config
mappers and `UiConfig_FillPair`; `UiConfig_CopyPair` remains byte-identical in
the original image. The original-based IPS replayed to the final image during
staging.

The stage manifest SHA-256 is
`4cf56358d3a0548adfdb85894fb4204903bb6364645e1afc30ff398f306dd7d7`. It pins
the original image `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`,
final image `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`,
composition manifest `577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`,
CCI `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`, and
standalone IPS `67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`.
The paired profile inventories are
`b7349a12e4557a5fb6d4778462f6f9a5e7ca91315a2a0bbe24036fda1ae67101` and
`14a9c7afb21cf3dfaebe39757cc83abb459ab2487f0fb6f753f2582b7e1f4587`; the
manifest certifies that the intended IPS is their only difference. GDB and RPC
are disabled in both profiles.

The 1,878,011,904-byte pinned CCI is a same-volume hard link from the approved
source to the stage root. `os.path.samefile` returned true, and the live
preflight independently hashed the staged path to the pinned CCI value. The
staging manifest records `storage: hardlink`. Existing callers of the general
staging helper keep copy behavior by default.

## Validation

- `python -m unittest tests.test_h2_azahar_rsp_probe.StagedGameFileTests tests.test_h2_manual_final_image_stage -v` — 14 passed.
- `python tools/h2_manual_final_image_stage.py ... --output E:\\SMT4decomp\\build\\h2-manual-comparison\\run-012` — exit 0; output manifest above.
- `python build/agent-work/H2-semantic/h2-manual-stage-shared-cci/run-002/checks/preflight_profiles.py` — exit 0; original and patched returned `ok: true` using the reviewed private observer binary `1bec8c3fef5b794e0abfe4bbbc1870202c562bb35ef3e49648b1d09060f8e6f1`.

No Azahar process was launched and no installed profile was accessed. Two earlier
staging attempts remain as incomplete run-010/run-011 directories; they were
preserved and not used. This packet validates staging and wrapper readiness,
not the runtime scenario. The next action is the user-controlled original then
patched interaction pass through the live CLI wrapper.
