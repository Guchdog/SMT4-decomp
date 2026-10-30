# H4 Navi callback call/return trace

## Result

The paired checkpoint run observed one invocation of `0x00399D60` in each profile. Both traces reached the caller LR at `0x001A95E8`, with all six GDB stops on thread `1`. The callback return register `r0` was `0` in both runs. The exact dynamic stop sequence was:

```text
0x00399D88 -> 0x00399D98 -> 0x00399DAC -> 0x00399DB8 -> 0x00399DCC -> 0x001A95E8
```

Other configured return sites (`0x00399DEC`, `0x00399E00`, and `0x00399E14`) were not reached in this invocation. Both callback traces ended with `callback_return_observed`; all temporary breakpoints were removed, there were no RSP timeouts, and the callback probe performed no guest-memory or register writes.

## Captured state

- At entry, `r0=0x086EB3C0`, `r1=0`, `r2=0x00399D60`; the host pointer at `0x0044CDF0` was `0x086EB380`, so the callback object was `host+0x40` in this sample. Entry `r3` was `0` in both runs.
- The range-validated callback object span `+0x00..+0x5F` was identical between profiles at entry, every reached return site, and callback exit. Its observed `+0x0C` word was `1` and `+0x10` was `0`; neither word changed during the call.
- The range-validated host fields at `host+0x30` and `host+0x38` were both zero. The pair at `host+0xB64` was `60 9d 39 00 00 00 00 00` (words `0x00399D60, 0`) in both profiles.
- `*[0x0043DA2C]` was `0x086FE980`; the bounded bytes at `+0x4B8..+0x4BE` were seven zero bytes in both profiles.
- The bounded `0x170`-byte view snapshot used the same pointer and contents across the two profiles at every trace event in this final pair. Pointer spans were validated before reads; null, invalid, and read-error fields are represented explicitly by the runner.
- At `0x001A95E8`, `r0=0` in both profiles. This is the observed return for this one checkpoint and is not a general return contract.

The GDB stop packets themselves include `thread:1`; the runner now extracts that ID directly from each stop reply. Static disassembly is consistent with the path: the `+0x0C` query at `0x00399D88` returned nonzero, the `+0x76` query at `0x00399D98` returned nonzero, the callback proceeded through `0x00220888` and `0x0039AF30`, and the latter returned zero before the callback returned. This observation does not resolve those helpers' broader contracts.

## Paired-run scope and repeatability

The accepted run used the private loopback Azahar build, isolated original/patched profiles, 250 menu callbacks, 250 field ticks, no axis override, and no physical input injection. Both profiles reached the field manager and all 250 ticks. The runner comparison reported equal title entry/state, save-load callback samples, post-confirm events/progress, field-scene signature, and tick counts. Both per-run staged-save hashes and non-mod profile manifests were unchanged. A read-only hash sample of the supplied source save `E:\emulador3ds\sdds4game1.sav` before run 004 and a post-run sample both yielded SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` (151,088 bytes). The pre-run console output was not persisted contemporaneously; the post-run audit records that provenance explicitly. The runner uses only staged saves under `C:\H4NaviProfile`, not the external source path. A post-run audit also recorded no Azahar process and no listeners on ports `54342/54343`.

An earlier successful exploratory pair (run `003`, before the final runner hash) also reached the callback and matched the field-scene signature, but its raw post-confirm event at the save-status setter differed in `r2` by one (`0x338` versus `0x337`) and three bytes at view offset `0x164..0x166` differed at the first callback stop. The final run `004` matched those captured fields. This is evidence of a dynamic timing-sensitive observation; it is not hidden by the final comparison.

Two earlier attempts with the runner's default 20 menu callbacks stopped before the load-confirm seam because the manager remained in state `1`; they did not reach the field checkpoint and are not runtime evidence. Reusing the known-good 250-callback checkpoint setting resolved that setup issue without changing the source save.

The offline-first evidence was reused after verifying its pinned code and source hashes: H3 placement/IPS round-trip and caller composition, H4 reader differential (119 cases, zero differences, negative control detected), and H4 camera composition (six cases, mutation detected). These narrow offline results do not establish whole-game equivalence.

## Artifacts and limits

- Paired capture: `build/agent-work/H4-semantic/h4-navi-callback-call-return-trace/001/checks/runtime-call-return-004/{report.json,original.json,patched.json}`.
- Hashed source-save/process/port audit: `build/agent-work/H4-semantic/h4-navi-callback-call-return-trace/001/checks/runtime-post-run-audit.json`. It pins the post-run source hash, records the pre-run hash observed before run 004 (and that its console output was not saved contemporaneously), verifies the staged copies, and captures process/port status after the run.
- Reused offline reports are copied under `build/agent-work/H4-semantic/h4-navi-callback-call-return-trace/001/checks/offline-*` for reproducible handoff provenance.
- Runner SHA-256 for the accepted run: `55186f05971cabf5abeb6d3c1a5d2ef6c518799785503462e305c672e99a8cbb`.

The trace establishes one bounded callback dispatch and return at this H4 checkpoint. It does not establish player movement, physical or logical input semantics, H4 target interaction, zone transition, helper contracts outside this invocation, or whole-game equivalence. No candidate implementation or production replacement is claimed.
