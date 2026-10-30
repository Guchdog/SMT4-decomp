# Independent review: H2 Thumb-corrected combined image

## Recommendation

**Ready for a fresh, isolated, user-controlled Azahar CLI runtime test.** The image and IPS are internally consistent and the corrected formatter pointer is present. This is test readiness only: runtime stability, visible Audio Settings behavior, callback scheduling, and persistence remain unverified.

## Artifact and patch audit

The pinned original image identity agrees with the packet and manifest: SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The final image is 3,633,152 bytes with SHA-256 `cd095feb4c8034874a2ef4661356cb131e0e240cfc907f454f12b83d05c13bf4`; the 4,727-byte IPS has SHA-256 `08dc412ae2045858cc5e087ca97527edd32622311c2bd0b9a219276fec7ba758`; and the manifest hash is `4002ab29da801d36eafd17fd728d0473f50d7d10ec6c786ba3135b6b431140cf`. All match the producer handoff and report pins.

I applied the IPS records in memory to the pinned original. All seven record offsets, lengths, and payload hashes agree with the manifest, and the result is byte-identical to the saved final image. The final image differs from run-013 at exactly one byte: file offset `0x1CB258`, `0x80` to `0x81`. This is the Thumb-state bit in the formatter function pointer. The new manifest records 4,006 changed bytes from the original; no claim of byte identity is made.

The manifest places Calc entry/body at `0x001EA928` and `0x003FE624` (2,096 bytes); Draw main at `0x002CAFD0` (1,464 bytes) returning at `0x002CB55C`; its helper and `%s\0` at `0x003FEE54` (124 bytes) and `0x003FEED0`; Secondary entry/body at `0x002CAEF0` and `0x003FEED4` (292 bytes); initializer at `0x002F4CA0`; and ready gate at `0x002FC0EC`. The shared cave `[0x003FE624,0x003FF000)` has 2,524 bytes. The Calc body consumes 2,096; rounded Draw helper/string tail consumes 128; Secondary consumes 292; total 2,516 with 8 bytes left. The Draw replacement's 1,464-byte write ends at `0x002CB588`, while its return instruction is before that endpoint and before the retained suffix. The saved manifest reports no replacement-entry reachability into the retained suffix and zero aligned absolute-pointer hits. These are static placement checks, not proof of all runtime control flow.

## Object and integrated offline evidence

The refreshed Draw object is SHA-256 `250598c55e1b175f1e9316425cc83810331340e92286346b8d5f87b9dd89adb4`; its source hash is `5ca7486aaa1244ae5e95b9e5073a7f1c49d1568cd6ad01139bc14bd86c0c0726`. Both match the reviewed production object record. The refreshed Secondary source hash is `56893b2c7e6fd76ffe5552d23483467e9ee6a34b7375a3f39d67d41da0d6d2fa`, and object hash is `681e67ee676c636d756e50f668101913ce344d7626b0efc31c9bd4888315e164`. Its translation unit/object changed since run-013, but the manifest's extracted selected-function hash remains `e2e714f635eee7874699fde891189dfed1298d225a21423554077152e66d4913`, identical to the prior reviewed manifest; it remains a 292-byte, zero-relocation body.

The integrated offline report hash is `b8d8394293cfad846e75cf9fccf2ec536ea1a312461cd63d91705c2bf14e5c8c`, and binds to the final image hash above. It reports Draw 46/46, Calc 16 persistent sequences and 54 ticks across seeds 7 and 20261024, Secondary 34/34, initializer 10/10, and ready gate 4/4. All five declared negative controls were detected: Draw helper target plus four, wrong Calc logical map, wrong Secondary count, wrong initializer sprite-group count, and always-ready gate. No offline counterexample is recorded. These are bounded ARM differential checks using matched HLE boundaries, not full application tests.

The caller-composition report hash is `0565bb05a18ddd002ee950208565ca33d5b55bb5c96f43a3074838c7f2a3610a`. It reports 3/3 State 9/10 cases and detects the wrong Calc callback address. Its scope is partial: real callback scheduling and most engine/service internals are represented by explicit HLEs.

## Limits and next action

A new isolated CLI runtime run is now a reasonable next step using this exact staged image/IPS and a fresh profile with GDB/RPC disabled. The user should control the scenario and host input. Record launch/profile/image hashes and observe entry into Audio Settings, rendering, navigation, cancel/confirm, and save/relaunch persistence. The previous image and Draw/Secondary split crashed at Audio Settings; this corrected build has not yet run in Azahar, so there is no evidence yet that the crash is fixed.

Renderer, cursor, layout, TBB, formatting/font, touch, callback scheduler, resource/service, and indirect callback behavior remain incompletely modeled or mocked. Caller tests do not schedule Calc, Draw, or Secondary. Save persistence, profile behavior, broader game stability, and whole-game equivalence remain open. Keep the H2 milestone open pending runtime evidence.

## Reviewer method

Read-only inspection only. I independently hashed the saved image, IPS, manifest, and objects; compared run-004 with run-013; checked the declared placement arithmetic and selected Secondary symbol identity; and replayed the serialized IPS in memory. The only commands were read-only PowerShell file reads and Python inspection scripts (`python -`), all exit 0. No tests, compiler, emulator, debugger, profile setup, board update, or implementation change was performed.
