# H2 corrected final image — manual runtime comparison

## Setup and identity

The user-controlled test ran the independently reviewed portable package
`E:\SMT4decomp\build\h2-manual-comparison\run-002` through the Azahar CLI.
The original and patched profiles were launched serially with their own
`app` directories as working directories and the same `pinned-title.cci`.
Both used Azahar SHA-256
`c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb` and CCI
SHA-256 `9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`.
The patched profile loaded IPS SHA-256
`bb9fc65956b2261468825a3732a2019cdd69226a6402309716bbeadfb26ac808`.
GDB and RPC were disabled in both profiles and the application logs.

Patched launches: PID 14284 at 22:48:42-04:00, PID 14728 after restart at
22:50:44-04:00, and PID 20212 for SE/Voice checks at 22:53:14-04:00. Original
launches recorded in this task were PID 24164 and PID 1836. Per-launch records
are in the adjacent `*-launch.json` files. The original endpoint launch record
is a compact record and has no IPS field because that profile has no patch.

The staged patched log confirms `Debugging_UseGdbstub: false` and that the
staged `code.ips` was applied to `code.bin`. The final original and patched
session logs were saved to `original-final-session.log` and
`patched-final-session.log`; their SHA-256 hashes are
`9fc3a2a4d5b54dac521118f84fd5ccbbffe6bd87efcecc9f4e96668e569ea508` and
`e3d2a4b6e892c82c84301c018c8e3af3e449635eb3240ea1091dcdd229497036`.
The final profile inventory is `profiles-after-runtime.json`, SHA-256
`64510ae699280a706808c1654a3fa9673e7ce6ba68d76628d6f91fda90ef060b`.
NAND configuration hash `03f9bb1edcc9f742774f1b66b66e6b10cc270eb8e7ae6881008ff9f876928f36`
matches the pristine seed and both final profiles. The title custom-config file
has hash `1c6e8b89795e80a5976540da8a9d45be8c03759bf903b537a15b7dd76b046f7c`
in both post-run profiles; it is not part of the pristine seed manifest.
Azahar-created logs, caches and runtime metadata differ as expected; these
files do not expose guest `g_ConfigBytes`.

## Human observations

These results were reported by the user operating the emulator. No keyboard or
mouse automation, debugger, RSP or RPC was used.

- The corrected patched image opened Audio Settings and stayed open. This
  resolves the earlier final-image attempt that closed at Audio Settings. The
  runtime result alone does not isolate which individual change fixed that
  failure.
- The user reported all three initial slider positions matched between the
  original and patched profiles.
- In the patched profile, moving BGM one notch and pressing B restored the
  previous BGM position and sound on reopening.
- In the patched profile, confirming a one-notch BGM change with A kept it on
  re-entry for that session. After closing and restarting the app, BGM returned
  to the starting value, matching the earlier original-profile result.
- In the patched profile, one-notch SE and Voice changes confirmed with A each
  remained visible after reopening during that session. Cross-restart
  persistence for SE and Voice was not checked.
- The user moved BGM, SE and Voice to Min and tried one step lower, then to Max
  and tried one step higher. All stopped at both endpoints in the patched
  profile. The user then confirmed all three also stopped at both endpoints in
  the original profile.
- The final original process (PID 1836) was closed at the user's request. No
  Azahar process remained at final inspection. A read-only Windows Application
  log query for Azahar crash events in the final test window returned zero
  records. Process exit codes were not captured.

## Result and remaining limits

This corrected image now demonstrates stable entry to the Audio Settings UI,
matching visible initial slider positions, cancel behavior for BGM, in-session
confirmation behavior for all three sliders, matching BGM restart behavior,
and matching endpoint clamping in the original and patched profiles. It also
shows that this profile's confirmed BGM setting is not persistent across an
Azahar restart, just as in the observed original profile.

This is partial, manually observed runtime evidence, not full H2 acceptance.
The test did not capture guest `g_ConfigBytes[0..2]`, exact slider values,
identical per-button input sequences/timing, restart persistence for SE and
Voice, or the callback scheduling and every service boundary. It does not
establish whole-game equivalence. The offline differential, caller-composition
and HLE-boundary limits remain as listed in
`h2-thumb-reintegrated-image.md`. H2 stays open for those unresolved criteria
and independent review of this runtime record.
