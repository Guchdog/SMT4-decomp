# H2 paired RSP lifecycle capture

## Result

The bounded original-versus-patched runtime scenario passed: both runs recorded the same 51 scripted logical actions and all 19 compared checkpoints matched. Both Azahar processes exited cleanly, restarted, and re-entered Audio Settings with the same default values.

This does not complete H2. The run report sets controlled_lifecycle_completed=false and h2_full_acceptance_supported=false. After confirmation, both original and patched stayed in TitleConfig state 2 for all 40 readiness checks (ready_return=0); same-session return to the title was not established. After process restart, both re-entered at state 1 with BGM/SE/Voice values 8/8/8, so neither persisted the confirmed 7/7/7 values. Their matching reset behavior is parity evidence, not proof of persistence.

## Frozen artifacts and prelaunch gates

The run-006 packet froze 30 inputs and two writable-file baselines; all hashes matched before launch. The offline and caller reports refer to the same final image and composition manifest:

- H2 final image: SHA-256 acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446.
- IPS: SHA-256 67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb.
- Composition manifest: SHA-256 577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27.
- Offline H2 aggregate: passed and bound to that image/manifest; report SHA-256 0ecd97778086ecee46df70af1b12d3ec5a5d2f023bb8962d451b90d96b92dfea.
- Same-image H2 caller composition: 3/3; image SHA matches; report SHA-256 fb4cae35d34e089211ac4404c011e25ec1b69c370dc03d75a9a36ee8b0157f1e.
- ARM/Thumb interworking, H2 differential, H2 caller and H3 caller gates were recorded as passed in the frozen prelaunch report. The selected H2 mapper and FillPair function bodies were separately recompiled and matched the exact image slots; whole-translation-unit hash warnings do not affect those selected bodies.

The private Azahar executable matched its delivery manifest at SHA-256 1b3bb3d0822d8c045cf4dc6157d0466f675706727fac3240b6fa3d579de49682. Its pinned GDB stub source matched SHA-256 bb345fcaca1e09f41a5d5f6941a4eef5d98e0b0257b15aa98ce993c0a22025d6 and binds to INADDR_LOOPBACK. The CCI SHA-256 was 9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2.

## Runtime observations

The paired run used separate disposable portable profiles and ports 62140 and 62141. Each process and its restart loaded the same pinned private Azahar executable. The report records process IDs, argv, working directories, executable hashes, CCI hashes, snapshots and logs.

Each side recorded 51 matching scripted actions and 19/19 matching state checkpoints with no mismatches. The route includes cancel and re-entry, all three rows, both directions, clamp checks at 0 and 10, returning to 7, and confirm at state 2. The input source calls UiListCursor_SetSelectedRow and substitutes a deterministic one-frame logical-query response; it does not prove physical controls or scheduler cadence.

After confirmation, both sides observed state 2 and values 7/7/7 for 40 checks; TitleConfig_IsReady returned 0 every time. After a clean process restart, both returned to state 1 with 8/8/8. The original and patched restart-persistence flags are both false, while their restart outcomes match. All four process exits were clean (exit code 0); all GDB listeners were gone after each exit.

The report confirms the profile seed, staged runtime DLLs/plugins and private Azahar executable were unchanged. The profile copies changed identically in host-side configuration and system metadata. The user save was not staged or loaded; this runner uses the CCI and only the two allowlisted profile seed files plus copied emulator configuration.

The emulator close prompt was disabled only in the two disposable staged qt-config.ini files so WM_CLOSE could exit without an interactive confirmation. Frame limiting and VSync were also disabled identically in those copies. The profile seed and the user's active emulator profile were not changed.

## Evidence files

- Runtime report: build/agent-work/H2-semantic/h2-rsp-lifecycle-parity-capture/run-006/runtime-output/autonomous-gdb-verification.json, SHA-256 10a273586056da555ba5be65c4397a186a9128dacc57f3ac566e0bf9c43d14bf.
- Original Azahar log: build/agent-work/H2-semantic/h2-rsp-lifecycle-parity-capture/run-006/runtime-output/original/azahar_log.txt, SHA-256 91439eab4295b69a783b9f8c4918ef7b2cf24a86e151a22f303d161d951d7a53.
- Patched Azahar log: build/agent-work/H2-semantic/h2-rsp-lifecycle-parity-capture/run-006/runtime-output/patched/azahar_log.txt, SHA-256 9f215abbae0fb6752d91e09c3645cc3178dbc0717837ddb009818cdb054cce57.

Earlier attempts are preserved in their run folders: run-004 exposed Windows path-length error 206 in the long checkout path; run-005 exposed the default-No host close prompt. The successful run used a short temporary path and the disposable-profile setting described above.

## Remaining H2 work

Keep H2 open. Resolve why the title readiness gate remains false after confirmation under this RSP-driven scenario, then validate same-session return and any actual stored setting bytes. The current logical-query stub and cursor setter do not establish real physical-input mapping, input cadence, or whole-game behavior. Any follow-up must keep the offline-first gate and isolated profiles, and must not stage the protected user save.