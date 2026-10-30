# H2 corrected RSP runtime evidence index

## Scope

This packet reruns the H2 logical-input sequence after the independent H0–H3
audit found that the earlier runner wrote the cursor selection at the wrong
offset. The corrected runner calls the original `UiListCursor_SetSelectedRow`
at `0x0029EDFC`, asserts the selected option's expected `TitleConfigWork` word
after every Calc frame, and records the scripted query response and state.

The runtime exercises the original `TitleConfig_Calc` with controlled logical
query responses. It does not establish physical controller mapping, callback
scheduling from the input manager, or persistence across a clean process
restart. The RSP driver starts original and patched staged profiles from the
same approved seed and uses the final H2+H3 image for the patched profile.

## Frozen identities

| Artifact | SHA-256 |
|---|---|
| Corrected runner `tools/h2_autonomous_gdb_verify.py` | `d5da4f9f3ce33f1c16504acc3fa707104c6b087608f407c8bab052c4e09d5040` |
| Original `code.bin` | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Final H2+H3 `code.h3-h2final.bin` | `81c1c6ae72d88b689cde3e9982439c8f8c4a6e8773887547f4cb85b86cd34a20` |
| Final H2+H3 IPS | `95846920df9ceb0e6395b6fb7e5358c99b83dd14e5861ffcfa80d8e64208eda5` |
| Private loopback Azahar | `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a` |
| CCI | `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2` |
| User-provided save before/after | `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` |

## Offline gates

- H2 ARM differential on final H2 image: passed; `46/46` Draw cases, `16/16`
  Calc sequences / `54/54` ticks, `34/34` Secondary cases, `10/10`
  initializer cases, and `4/4` ready-gate cases. The negative controls passed.
- H2 State-9/10 caller composition on the H2 final image: passed `3/3`; the
  wrong-callback negative control was detected.
- H3 final-image caller composition on the H2+H3 image: passed; the caller
  target remains ARM-aligned and the wrong-next-state control was detected.

## Paired runtime artifacts

All outputs are under
`E:\SMT4decomp\build\h0-h3-closure-20261028\`:

| Artifact | SHA-256 |
|---|---|
| `h2-rsp-corrected-run001/autonomous-gdb-verification.json` | `cb9c9e123dc4e56961dfe0997d2f671bb35a4254dd6c5018ceedb1d8705cfd4a` |
| `checks/h2-differential-rerun001/report.json` | `111b454e4ad68867c9c05815371a8b24e8a9f27c08596ace6e29e804d1a3ea89` |
| `checks/h2-caller/report.json` | `1f231771662e7f2c3b86667c5dca1565e8d0fb770ae8d113d9239368f7687e57` |
| `checks/h3-caller-rerun001/report.json` | `ef83eb50372d02a5bf86bd71039b2758c0fd4466d39249bf5f634da8372e1cc1` |

The runtime report records host and guest PIDs, each staged executable path and
hash, the loopback ports, CCI pins, final image/IPS pins, 12 checkpoint pairs,
and all 29 scripted logical actions. The `scripted_input_traces_equal` field is
true and `passed` is true. Each action's selected work word is checked against
the expected value before the run can complete. Both processes exited under
the runner's child-process cleanup path; ports `60940` and `60941` were closed
after the run. The save hash above was rechecked after runtime.

## Independent review requested

Verify the listed hashes and the 29 actions / 12 checkpoints from the raw JSON.
Confirm that SE changes `TitleConfigWork+0x2C` and Voice changes `+0x30`, while
BGM changes `+0x28`; distinguish this scripted logical-query test from physical
input behavior. Do not broaden H2's status beyond the resulting evidence.
