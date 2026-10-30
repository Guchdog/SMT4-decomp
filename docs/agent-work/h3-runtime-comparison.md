# H3 runtime comparison — known-save happy path

## Result

The same supplied save reached the **Shinjuku Station — Underground** field in
the original and the H1/H2/H3 composed image. The final original and patched
screenshots show the 3D station entrance and the same lower-screen map. The
runtime evidence supports this one known-save route. Separate paired runs also
reject an empty slot, return to the title menu on cancel, and reproduce an
internal missing-file failure result at the original open boundary. H3 is closed
for its bounded title handoff scope; the save reader and validator remain
original dependencies. Independent reviews accepted these bounded results.

## Frozen inputs and isolation

- Source save: `E:\emulador3ds\sdds4game1.sav`, 151,088 bytes,
  SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`.
- Original and patched private profiles each used a byte-identical copy at the
  title's `data/00000001/sdds4game1.sav` path. The staged copy hash matched the
  source before and after both runs; the profile's other user files were
  unchanged.
- Both runs used the same decrypted US v0.1.0 CCI and private loopback-bound
  Azahar executable (SHA-256
  `8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a`). The
  patched profile used IPS SHA-256
  `b11128bd8b6510accb502f15423fabc5cf69999b01610ed7aadff31f5d5a7b8e`; its
  final image SHA-256 is
  `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`.
- No source save, live Azahar profile, or installed game files were modified.
- The two profile trees were unchanged within each run; they were not identical
  across runs. Six entries differ between original and patched baselines:
  `config/qt-config.ini`, each run's Azahar stdout/stderr logs, the two OpenGL
  shader caches, and `sysdata/play_time.bin`. The paired save fixture itself
  was byte-identical.

The offline differential, caller-composition, interworking, and independent
final-image gates passed before these emulator runs. Runtime output is in
[`runtime-field-settle-016`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-field-settle-016/).

## Observed route and checkpoints

1. Both profiles entered title state 8 with equal captured title state and
   equal save/load UI callback snapshots. The save UI recognized slot 0 as
   populated and displayed the character name **Flynn**.
2. One logical trigger-0 result was supplied only after state 2, selected slot
   0, its populated flag, and nonempty slot text were observed. Both profiles
   entered the original save-read path. The I/O worker, validation helper, and
   status setter were reached in the same order; the final status bytes were
   `01 00 00 01` in both. The save itself remained unchanged.
3. The game displayed **Load complete**. A second trigger-0 result was supplied
   once after observing that message, save UI state 5, and those successful
   status bytes. The callback returned and both profiles reached
   `Map_Field3DManager` (`0x00208CE8`).
4. The field-manager entry registers matched: `r0=0x3B`, `r1=r2=0x4096CBE4`,
   `r3=3`. Across 250 matched callbacks, `r0` progressed from `0x3B` to `0` in
   both profiles. The final screenshots show the same Shinjuku Station —
   Underground scene and lower-screen map:

   - [Original field screenshot](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-field-settle-016/original/field-scene-screen_small.png)
   - [Patched field screenshot](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-field-settle-016/patched/field-scene-screen_small.png)

The final screen files have different PNG hashes because capture timing and
render statistics differ; visual inspection shows the same field entrance and
map. A shorter 70-callback capture initially showed a black 3D top screen in the
patched run. Extending both runs to 250 matched callbacks produced the scene in
both, so the shorter capture was premature.

## Evidence and limits

- Machine-readable comparison: `build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-field-settle-016/report.json`.
- Independent edge-case review: [`h3-runtime-edge-review.md`](h3-runtime-edge-review.md).
- Original and patched event logs differ only in the I/O worker's `r3` buffer
  address (`0x873CD00` versus `0x873CC80`); event order, other captured
  registers, status bytes, UI progress, and field-manager sequence match.
- Azahar rejected a direct memory read of the field context argument at
  `0x4096CBE4` (`E0E`). The report therefore does not claim player coordinates,
  orientation, or a decoded map-area field from that address. The destination
  label is established by the captured screen, and the manager callback by its
  breakpoint and register sequence.
- Save-file parsing and I/O remain original dependencies. This test establishes
  a reproducible happy path for this one save, not all save versions or failure
  behaviors, and it is not whole-game equivalence.

## Bounded edge cases

- **Empty slot 1:** in
  [`runtime-empty-slot-018`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-empty-slot-018/),
  both runs observed an inactive slot and zeroed 0x12-byte name. One trigger-0
  result left the load UI in state 2; neither run started the save process or
  reached the field manager. The supplied save and each profile stayed
  unchanged.
- **Cancel from populated slot 0:** in
  [`runtime-cancel-state-020`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-cancel-state-020/),
  trigger 1 changed the UI work state from 2 to 3. After five callbacks the
  title work record was at `+0x9C=5`, the visible screen was the title menu, and
  neither run entered the save process or field manager. Save/profile hashes
  stayed unchanged. The title-menu capture is
  [`original/load-stall-screen_small.png`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-cancel-state-020/original/load-stall-screen_small.png).
- **Malformed-payload negative control:** in
  [`runtime-zero-payload-load-036`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-zero-payload-load-036/),
  isolated copies kept the first `0x100` bytes and zeroed the remaining payload.
  Both still listed Flynn and showed `Load complete`; after acknowledging that
  prompt, neither reached `Map_Field3DManager` within the bounded run. The
  original status setter still received `r0=1`, so this does not demonstrate a
  read-error response. Both staged files were restored byte-for-byte.
- **Earlier read-error probes:** removing the staged file at process start
  produced the state-7 result marker but did not capture the low-level open
  return. The first before-confirm probe also lacked the open-boundary capture.
  The later paired run below closes that evidence gap. See
  [`runtime-missing-before-confirm-037`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-missing-before-confirm-037/).
  The runner also attempted to set setter `r0=0` in a separate probe, but that
  paired JSON has no post-write register read-back; both runs still reached the
  field. The earlier reports remain bounded to their captured signals.
- **Missing-file open-boundary result:** in
  `build/agent-work/H3-semantic/h3-runtime-comparison/run-002/runtime-missing-before-confirm-044/`,
  each staged save was renamed after slot enumeration and before confirmation,
  then restored before `0x002C5948`. At `0x002D8E60`, immediately after the
  original open call, both original and patched runs had `r0=0`. At the status
  setter, both had `global_43e2f0=0100000000000000`, matching state 7's
  `+3=0` failure result in `0x002EF9AC`; neither reached the field manager.
  The status setter still received `r0=1`, which is a separate flag argument.
  Independent review found the only raw event difference was setter `r2`
  (`0x2A1` original, `0x2A0` patched); its meaning is unresolved. Both staged
  saves were restored, remained 151,088 bytes with the fixture hash, and profile
  integrity was reported unchanged. The screen capture failed, so this does not
  establish a user-visible error message. The concise machine comparison is
  `report.json` in that directory. The three JSON files were copied unchanged
  from the isolated writable run location into this checkout's ignored
  `build/` tree after capture.
- The `Load complete` prompt is captured in
  [`runtime-load-focused-011/original/load-stall-screen_small.png`](../../build/agent-work/H3-semantic/h3-runtime-comparison/run-001/runtime-load-focused-011/original/load-stall-screen_small.png)
  (SHA-256 `3c5e54533536ddd98bb7d0bd9909d7caa8ee7125f519575f2d019caf43778c91`).
