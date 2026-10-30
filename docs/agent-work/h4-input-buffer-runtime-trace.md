# H4 input-buffer runtime trace

## Result

The autonomous paired run reached the saved Shinjuku field scene in both the original and H3-patched profiles. It advanced 250 field-manager callbacks in each run, then observed all four configured breakpoints: `0x001078E8`, `0x001078EC`, `0x0011C640`, and `0x0011C644`. At each probe, the 32-byte primary-record region `0x004E3C28..0x004E3C47` and the separate 16-byte alternate record `0x004E3C48..0x004E3C57` were all zero at entry and stop. A 48-byte snapshot starting at `0x004E3C28` was recorded; it spans both regions. The 31-word table at `0x004E3C58..0x004E3CD3` was also zero. The manager prefix and calibration pointer/data matched between original and patched captures.

This is a neutral/no-input observation only. No physical or frontend control event was delivered, so it does not establish the producer's behavior under active input or identify the input source. The observations do confirm the statically mapped refresh path ran in the loaded scene and did not leave a nonzero sample in the observed window. The four probes were visited sequentially after the 250 scene ticks; they are not a per-frame trace of each address.

## Paired comparison and preservation

Both runs reached the field manager and recorded 250 ticks. The title entry, load callbacks, post-confirm events/progress, load-complete acknowledgement, and the runner's limited field callback signature comparison passed. The full captured view prefix was not byte-identical: three bytes at view offset `+0x164..+0x166` differed, with no field meaning established. The staged save before and after each run was 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; the staged non-mod profile files were unchanged within each run. The source save at `E:\emulador3ds\sdds4game1.sav` retained that same SHA-256: it matched the known pre-run fixture hash and a separate post-run read-only check, recorded in the ignored `build/agent-work/H4-semantic/h4-runtime-buffer-capture/run-001/source-save-integrity.json`. The runtime JSON itself contains hashes only for staged copies. Azahar was closed after the run.

The detailed report is `build/agent-work/H4-semantic/h4-runtime-buffer-capture/run-001/checks/runtime-input-trace-007/report.json`, SHA-256 `9cee1c43ae14a71337c95e8dc88db1b3214dec83bd793cd478638ea00d780fe0`. It includes registers, pointers, calibration bytes, stack context, view state, all requested probe snapshots, per-run save hashes, and the paired comparison flags. The read-only snapshot support is in `tools/h3_autonomous_verify.py` (`axis_input_snapshot`).

## Interpretation and limits

- `0x001078E8` receives `0x004E3BE8` in `r0` (the pointer loaded from `0x004650A0`) and primary-buffer pointer `0x004E3C28` in `r1`; `0x0011C640` receives source `0x10000000`, destination `0x004E3C28`, and count `1`. This is consistent with the static one-record copy path in `h4-input-buffer-producers.md`. `0x004E3BE8` is not the separate alternate sample at `0x004E3C48`.
- The captured primary record, alternate record, and counter table were zero in both runs. That does not show the frontend/device producer returned zero, because the experiment delivered no active input.
- This trace does not validate player movement, physical input mapping, active refresh cadence, or an H4 candidate. The matching callback signatures do not imply byte-identical field state; the three differing view bytes remain unexplained. Do not treat the neutral comparison as movement or whole-scene equivalence.
- Earlier controlled values at the return of `0x0027FBC8` changed only its camera-call stack outputs and bypassed the sample buffers; those tests remain separate evidence in `h4-live-input-observation.md`.

## Next step

Identify a safe, autonomous way to inject one bounded input event into the private emulator session without editing the user save or claiming a physical control mapping. First trace the input source object/ring state at the producer and validate any synthetic source mutation with read-back and a neutral negative control. Then correlate the resulting 16-byte sample with the axis reader and a candidate player-state update. Do not begin movement-path promotion until the event is observed at the producer and its effect is reproducible.
