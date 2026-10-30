# Independent review: H2 five-function final image — run-001

## Decision

**Pass for the bounded offline integration, with a provenance clarification for the caller report.** I independently verified the run-013 image/IPS and reproducibility artifacts; all five production symbols and the copied initializer pool agree with the manifest after the declared relocation edits. All five final-address comparisons pass and each reported negative control is detected. Ledger classifications for all five changed functions are `non_matching`, consistent with the changed bytes.

This supports the reconstructed functions under their explicit helper models. It does not establish real scheduler execution, rendered UI, physical input, settings edit/cancel/confirm behavior, save persistence, restart behavior, or Azahar runtime equivalence.

## Artifact identity and IPS reapplication

All hashes in this review's run-001 `task.json` matched before inspection. I recomputed the final run-013 identities and compared the independent reproduction build:

| Artifact | SHA-256 |
| --- | --- |
| Pinned `code.bin` (3,633,152 bytes) | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Final image | `7b2bc2983a890e1c4cf1ae71beca9f574260d98d6cfcdffb3bbb34bd3eb2b291` |
| IPS | `3901823e725afb914a9bc49c5f86038f8c285c107eedaa3a4337a64bc5b062d3` |
| Manifest | `e866f14b9c5bcf0936afa67aadabfcf58fff47e20e37ae51802dfd75745fc298` |
| Final-address report | `336ba06a4a338cb805cd5b6bfcfd042ccfc7ea094ddecd11fbc3ebb0e021197a` |
| Caller report | `5606654680b6083645086de13eea9e550c7b14398461b36995adf34cfb7af0cf` |

The final and `combined-build-repro-001` image bytes, IPS bytes, and manifest bytes are identical. I independently decoded the IPS stream, applied its seven records to the pinned original, and got the final image byte-for-byte. Record offsets, lengths, and payload SHA-256 values match the manifest; the IPS ends at `EOF` with no trailing bytes. The image has 4,006 differing bytes, all inside these declared records:

| File offset | Length | Purpose |
| --- | ---: | --- |
| `0x000EA928` | 4 | Calc entry branch |
| `0x001CAEF0` | 4 | Secondary entry branch |
| `0x001CAFD0` | 1,464 | Draw main body |
| `0x001F4CA0` | 572 | Initializer body |
| `0x001FC0EC` | 48 | Ready-gate body |
| `0x002FE624` | 2,524 | Executable page-tail cave |
| `0x0032AB78` | 68 | Initializer strings in the `.rodata` tail |

## Production symbol and placement checks

I rehashed each production source/object and extracted the five named symbols from those objects. Every source/object hash matches the manifest. I reconstructed the relocated symbol bytes and verified each final image body byte-for-byte:

| Function | Final placement | Extracted bytes | Source SHA-256 | Object SHA-256 | Relocation verification |
| --- | --- | ---: | --- | --- | --- |
| Calc `script_vm_func_001ea928` | body `0x003FE624`; entry `0x001EA928` branches there | 2,096 | `c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7` | `94197ad141393099a25e679b73457f127c54c7155fa4d8c2ff25270f8ca620fd` | Four local absolute pointers resolve to `0x003FE670`, `0x003FE7E4`, `0x003FE790`, and `0x003FE7C8`; final body matches with these values applied. |
| Draw `ui_func_002cafd0` | main in place at `0x002CAFD0`; helper `0x003FEE54`; format `0x003FEED0` | 1,464 | `e5c6414cd37d2d6fc9928ca85eb5466a8c07bcec224a887616cb383ac408d64c` | `0513196e3d93398036feba0177fc92cadadba87589068dc0605da64b0658ede2` | Seven helper calls decode to `0x003FEE54`; the format pointer at body offset 1460 resolves to `0x003FEED0`. |
| Secondary `engine_func_002caef0` | entry `0x002CAEF0` branches to body `0x003FEED4` | 292 | `3ca4676613634ae91fe980e5e6e3c79fa74aff355e0facc50149749ba10b9c37` | `e04b6dcb9ae560efa2e39202b04763263b03f1f61455efe5b54756ffda81d53e` | Zero relocations; object symbol equals final body bytes. |
| Initializer `titleConfig_func_002f4ca0` | in place at `0x002F4CA0` | 572 | `11b5360c77aecb4ab0e510774fd42a1cb479e8343aff4bb1a30d4cadeccc1b5e` | `432664ba70073ff98c2fed19559d4f663f0e4dd9732c519e1bf66eda4dcfe82d` | Zero relocations; object symbol equals final body bytes. |
| Ready gate `ui_func_002fc0ec` | in place at `0x002FC0EC` | 48 | `609aaf963db8129a560293c8d1e65b3c6df8fa016673d28b0143535dadb4e4ee` | `2c0ca7a51729389cce55cf31476f9a3075b50b3b4ef3cabebba9cffe0382b37d` | The call at `0x002FC108` decodes to `0x002BF41C`. The original four-byte tail `[0x002FC11C,0x002FC120)` is preserved. |

Both entry branches decode correctly: Calc `0x001EA928 -> 0x003FE624` (`0xEA084F3D`) and Secondary `0x002CAEF0 -> 0x003FEED4` (`0xEA04CFF7`). Draw's retained original suffix `[0x002CB588,0x002CB75C)` is byte-identical to the pinned original. Its earlier independent audit covers old main-to-suffix edges, direct branches, aligned absolute pointers, and the suffix back-edge; this review relies on that static audit and does not expand it to computed/indirect entries.

The cave map is contiguous and in bounds: Calc occupies `[0x003FE624,0x003FEE54)`, Draw helper `[0x003FEE54,0x003FEED0)`, `%s\0` at `0x003FEED0` followed by one alignment byte, and Secondary `[0x003FEED4,0x003FEFF8)`. This uses 2,516 of the 2,524 cave bytes and leaves 8 bytes.

Initializer pool bytes match the manifest payload and slots exactly. The pool has 68 bytes at VMA `0x0042AB78` / file offset `0x0032AB78`; it contains `TITLE_CONFIG_MAIN\0`, `TITLE_CONFIG D\0`, `camp/config.bf\0`, and `camp/config.mbm\0` in 20-, 16-, 16-, and 16-byte zero-padded slots. The corresponding original image region is zero-filled. The final mapped artifact confirms these bytes, but the loader's runtime mapping and page protection still need emulator verification.

## Final-address differential results

The frozen final-validation report is hash-bound to the pinned original, the final image, and `tools/h2_combined_offline_validation.py`. All positive cases have no first counterexample; each negative control is detected:

| Function | Positive results | Negative control |
| --- | --- | --- |
| Calc | 16/16 persistent sequences, 54/54 ticks across seeds 7 and 20261024 | Wrong logical map `4:0 -> 3:0`, detected as a work-state difference. |
| Draw | 46/46 directed cases | First helper-call target plus four, detected as an invalid instruction. |
| Secondary | 34/34 directed cases, 17 per seed (7, 20261024) | Wrong-count mutant at final VMA `0x003FEED4`, reached through the patched entry, detected on `both-loops-distinct` as changed helper arguments/order. |
| Initializer | 10/10 cases, five per seed (7, 20261024) | Wrong group count `0x17` at the original entry, detected as a work difference. The control uses a separately compiled candidate body with its task-name pointer retargeted to the copied pool; the positive comparisons execute the production body from the final image. |
| Ready gate | 4/4 directed cases | Always-ready result at final ready-gate VMA, detected on `task-still-registered` as a return mismatch. |

These checks compare the specific callback state, arguments/traces, and ABI fields defined by their runners. Helper implementations outside each tested body remain original or modeled boundaries; these are not whole-function engine simulations.

## State-9/10 caller composition

The caller report identifies the exact combined image and manifest and sets `production_initializer_mode: true`. The runner maps the patched image and passes `candidate=None` to the positive `CallerMachine`; therefore those three positive cases execute the in-image production initializer at `0x002F4CA0` and the production ready gate at `0x002FC0EC`. The cases pass with matching observed phase states `[10,10,5]`, `[10,10,5]`, and `[9]`.

One provenance field needs clarification: the caller report's root `source_sha256` and `object_sha256` refer to a separately compiled `h2_init_orchestration_candidate.cpp` artifact. The runner still compiles it in final-initializer mode to construct the wrong-Calc-callback control, but does not inject it in the positive patched runs. Those fields should not be cited as the identity of the production initializer; the manifest's `initializer` source/object/symbol hashes are the production identity. The caller control also uses that injected candidate path, so it demonstrates caller sensitivity to the callback tuple but is not a mutation of the exact production image. This does not invalidate the three positive exact-image caller cases or the production initializer's separate final-address wrong-count control.

Caller coverage remains limited to State 9, pending State 10, ready/reset, and the flag gate. Allocation, task creation/registration, task-active lookup, sprite/cursor/resource setup, sound/reset, transition, and other named services are HLEs. It compares registration tuples and work/handle linkage, but never schedules Calc, Draw, or Secondary callbacks. No visible UI, physical input, settings edit/cancel/confirm, persistence, profile isolation, restart, or Azahar behavior is shown.

## Function records, ledger, and recommendation

All five ledger rows are currently `non_matching`, with their original code addresses/extents and source mappings retained: Calc 1,796 bytes, Draw 1,932, Secondary 224, initializer 572, ready gate 52. This correctly describes their changed bytes without implying semantic or runtime completion. Their function records describe bounded behavior and dependencies; the final-image report supplies a consistent current placement and image-level record.

The initializer record includes older run-001 wording that production compilation alone did not prove differential behavior and a candidate-only historical line saying the then-current ledger was unchanged. A later run-013 section records the final production differential and caller evidence, and the current ledger is `non_matching`; the historical language is chronologically understandable but should be made explicit as superseded to avoid a contradictory skim. The Draw record still cites the earlier Calc+Draw image as its production integration artifact; the newer five-function report supersedes that image for final placement, while the Draw body/source hashes remain consistent.

Recommendation: accept the five-function offline artifact and bounded final-address evidence for integration review, keeping all five ledger classifications `non_matching`. Before treating the function-record set as a concise final summary, clarify the caller report's candidate `source_sha256`/`object_sha256` fields and mark the earlier initializer-only evidence as superseded by run-013. Do not describe H2 as runtime-complete until scheduler execution, UI input/edit/cancel/confirm, saved configuration, and restart persistence are tested against original and patched images under isolated profiles.
