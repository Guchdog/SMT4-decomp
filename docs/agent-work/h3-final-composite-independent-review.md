# Independent review: final H2+H3 composition

## Finding

The final H2+H3 artifacts and the requested bounded runtime observations are internally consistent. The combined image applies the H3 title-entry window over the reviewed H2 base; the IPS reproduces the combined image exactly. The offline caller check and 12 H2 runtime checkpoints pass. The known-save route reaches load acknowledgement and the field manager in both profiles, with 250 field callbacks each. The separate post-open read-error trace shows the original read returning zero after a successful open, but it does **not** establish a final load-status marker, success acknowledgement, field-manager entry, or visible error.

## Evidence manifest

I recomputed all nine manifest entry sizes and SHA-256 digests. Every entry matches:

| Evidence file | Bytes | SHA-256 |
| --- | ---: | --- |
| `composition.json` | 670 | `b7bce10550608004ae45bad2cd06803af201900a69caa2a4b59bb7256d7f1006` |
| `caller-final-report.json` | 20,740 | `12f42799611f1fe918a5a8721ff3264f1be5ea0793dea071a7f4818559657ef6` |
| `h2-regression-report.json` | 50,473 | `21000529832d7c40104eeed1258c696aeb8d133de4e81662b18208020ff3e138` |
| `read-error-report.json` | 30,827 | `adb543faa6b31f6b59b803828902576f6418c1833a3bc711feca0c94ca03b326` |
| `read-error-original.json` | 213,464 | `36dca190889f81b3e0d2a7b473602cdc1b3d3fbbbe96348628038846fefde672` |
| `read-error-patched.json` | 213,463 | `2cbee62205a6851cf61d89c63f6e31ac7e3da5221fb60d8bd467887f82139fdd` |
| `known-save-report.json` | 264,355 | `d653259f803e9cb5814b12da849bda44595fb17f00b47b0462db704eed7c36e5` |
| `known-save-original.json` | 314,851 | `ba72612d779a3afb5397fb895ddc289da5a1c0d3b873423e1aee498042cffd95` |
| `known-save-patched.json` | 314,848 | `a41f9601aa52934cc28a60014a5b893138d7083fed93f193b470663393d4f87f` |

## Image composition and offline caller

I independently hashed and applied the actual artifacts at `E:\SMT4decomp\build\agent-work\H3-semantic\h3-final-h2base-revalidation-20261028\`:

- H2 base `code.h2-final.bin`: 3,633,152 bytes, SHA-256 `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`.
- Combined `code.h3-h2final.bin`: 3,633,152 bytes, SHA-256 `81c1c6ae72d88b689cde3e9982439c8f8c4a6e8773887547f4cb85b86cd34a20`.
- `code.h3-h2final.ips`: 7,030 bytes, SHA-256 `95846920df9ceb0e6395b6fb7e5358c99b83dd14e5861ffcfa80d8e64208eda5`.

Parsing and applying the 543 IPS records to the H2 base yields the combined image byte-for-byte. All 89 differing image bytes fall within the 120-byte H3 window at virtual `[0x0030A9A4,0x0030AA1C)` (file offset `[0x20A9A4,0x20AA1C)`); all bytes outside it match the H2 base. This independently supports the recorded round-trip and outside-window metadata.

The offline caller report at `0x0030A9A4`, entered from `0x001EA32C`, reports the original/candidate/in-place results equivalent for the listed state, work/manager, return, stop, fault, and call-sequence fields. Its nonzero guard skips the entry in both original and candidate, and its negative control changing the next state to 7 is detected. This is a bounded Unicorn composition with deterministic dependency stubs; it does not cover state-8 polling or downstream save/load behavior.

## H2 runtime checkpoints

The H2 regression report has `passed=true`, and its final image and IPS hashes match the composition metadata above. All 12 checkpoint comparisons pass: `initial_entry`, `bgm_dec_5_to_4`, `bgm_b_cancel_triggered`, `reentry_after_cancel`, `bgm_min_clamp_step_6`, `bgm_y_default_reset`, `bgm_set_to_4`, `se_set_to_4`, `voice_set_to_4`, `voice_max_clamp_step_7`, `voice_restore_to_4_step_6`, and `a_confirm_state2`. Each reports normalized `TitleConfigWork` equality and equal `g_ConfigBytes`; the checkpoint values cover the recorded BGM, SE, and voice transitions and clamps.

## Known-save runtime route

In the separate known-save run, original and patched each record open `r0=1`, requested size `0x24E30`, and `AsdSave_Read` return `r0=1`. Both record the controlled load-complete acknowledgement (`return_value=1`) and field-manager entry. The report compares 250 field callbacks in each run and marks field-scene semantics equal. Both staged saves and non-mod profile trees are reported unchanged. This supports the known-save route for this fixture and captured scenario; no screen image is present in these copied run records, and this is not whole-game equivalence.

## Post-open read-failure route

The raw paired events show, in both original and patched runs:

- open at `0x002D8E60`: `r0=1`;
- requested read size at `0x00210474`: `r3=0x24E30`;
- original `AsdSave_Read` return at `0x00210478`: `r0=0`;
- follow-up `save_validation_return`: `r0=1`;
- `save_reader_flag_clear`: `r0=6`.

The disposable staged save was truncated after successful open, then restored before the status setter; final staged save and profile snapshots are unchanged in both records. These observations distinguish a post-open short/read failure from an open failure. They do not establish what the follow-up validator's `r0=1` means beyond its observed value.

The error report is correctly only `status="observed"`, but its generic comparison booleans `real_read_error_reproduced_both`, `load_result_flag_zero_both`, and `load_result_flag_one_both` are false: that runner's derived predicates are for missing-file/open-failure cases and do not classify this after-open truncation case. I therefore rely on the raw breakpoint events for the bounded read result, not those derived flags. The sampled progress record contains `global_43e2f0=0100000000000000`, but the read-error route does not capture a terminal status write that would justify assigning it as the final outcome marker. It also records no acknowledgement, no field-manager entry, and no screen capture (`post_read_screen=null`). No visible error or final user-facing failure contract is established.

## Prior review scope and limits

I read `docs/agent-work/h3-read-return-independent-review.md` (SHA-256 `63e30c8d514957b48d863f4f89f17269745021cd6cd5fd9c35bd84b5d17fcf66`). It reviews a separate earlier evidence packet. Its interpretation of that packet's progress bytes as a state-7 failure marker is not imported into this composition review's distinct post-open trace. Here the raw open/read/validator/flag-clear breakpoints are the evidence, and the final status remains unresolved.

Overall evidence supports the exact image composition, bounded offline caller composition, H2 title-config runtime checkpoints, known-save route, and observed post-open reader result on the supplied fixture. Parser/I/O implementation, final status semantics for the error route, visible error behavior, broader input domains, and whole-game equivalence remain unproven.

## Review procedure

- Validated manifest byte counts and digests using Python standard-library `json`, `hashlib`, and `Path.read_bytes()`; all nine passed.
- Recomputed H2 base, combined image, and IPS hashes; parsed and applied the IPS records and compared the resulting bytes with the combined image; all checks passed.
- Extracted the 12 checkpoint comparisons and selected raw events/snapshots from the listed JSON reports using Python standard-library JSON parsing; exit 0.
- No emulator, build, production-code edit, or board edit was performed.
