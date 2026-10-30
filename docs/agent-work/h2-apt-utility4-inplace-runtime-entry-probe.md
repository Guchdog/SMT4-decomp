# H2 APT Utility-4: paired runtime entry probe

## Result

The reviewed H2 base and the same image with the 40-byte APT Utility-4 candidate both reached the live entry **0x002C0EFC** and then the original wrapper **0x002B5A1C** in Azahar. At the wrapper boundary, both supplied the six AAPCS argument words **(4, 0, 0, 0, 0, 0)**, had **LR=0x002C0F20**, and had 8-byte-aligned **SP=0x0FFFFEF0**. Both entry LR values were **0x00103E84**, consistent with the previously observed title caller path. Runtime bytes at the 44-byte entry span matched the selected pinned image for each run.

The candidate image and original-based IPS remain experimental. This proves only the bounded entry-to-wrapper dispatch on this observed ARM caller path; it does not establish wrapper/service behavior or whole-game equivalence.

## Frozen inputs and gates

| Input | SHA-256 |
| --- | --- |
| Private loopback Azahar | 8e18aac0df0be63b3351fb4b39b6d5f75fb23992ce3ad9d8ccd8cb671dc6f60a |
| Original code.bin | 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558 |
| Reviewed H2 base image | acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446 |
| H2 base IPS | 67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb |
| H2 base plus candidate image | 788530a1b1ad7d4f361228cbd0e4b87885b37606a8f3485c52e5390ae3223179 |
| H2 base plus candidate IPS | 9c4f38fbdefc9c52bc745e4cbb1e6425d5822db7c2ed2267331d582c5a841c88 |
| Pinned CCI | 9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2 |
| Disposable save fixture | 6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9 |
| Protected user save before/after | 6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9 |

The preflight verified six gates: direct ARM differential, caller composition against the pinned original, caller composition against the reviewed H2 base, observed caller-context composition, aligned ARM/Thumb immediate-target scan, and independent IPS package review. All passed. The scan found seven direct ARM callers and no immediate Thumb-2 BL/BLX target in the scanned text; indirect or alternate-state callers remain outside that result. Four source-identity warnings in the inherited H2 base remain visible (three mapper entries and FillPair).

The runtime used ports 62180 and 62181; both exact child PIDs owned listeners bound to 127.0.0.1. Separate portable app profiles were staged. Each profile received a copy of the pinned disposable fixture; Azahar was not passed the user-supplied E:\emulador3ds\sdds4game1.sav. That file and the fixture retained their hashes. The probe used temporary RSP software breakpoints only, with no M/P/X memory-write packets and no logical input injection.

## Captures

| Image | Entry PC / LR | Wrapper PC / LR | Six arguments | Runtime entry bytes | Patch log |
| --- | --- | --- | --- | --- | --- |
| Reviewed H2 base | 0x002C0EFC / 0x00103E84 | 0x002B5A1C / 0x002C0F20 | (4,0,0,0,0,0) | matched base image | present |
| H2 base plus candidate | 0x002C0EFC / 0x00103E84 | 0x002B5A1C / 0x002C0F20 | (4,0,0,0,0,0) | matched candidate image | present |

Both processes were stopped at wrapper entry and then terminated by the bounded probe. The report does not claim a clean emulator shutdown. No listener remained afterward.

## Reproduction

Run the focused contract tests:

~~~powershell
python -B -m pytest -p no:cacheprovider -q tests/test_h2_apt_utility4_inplace_runtime_probe.py
~~~

Run the paired entry probe:

~~~powershell
python -B tools/h2_apt_utility4_inplace_runtime_probe.py --output-dir build/agent-work/H2-semantic/h2-apt-utility4-inplace-runtime-probe/run-002/runtime --base-port 62180 --startup-timeout 45 --capture-timeout 45
~~~

The source, report and gate attestation are under tools/h2_apt_utility4_inplace_runtime_probe.py, build/agent-work/H2-semantic/h2-apt-utility4-inplace-runtime-probe/run-002/runtime/runtime-entry-comparison.json, and build/agent-work/H2-semantic/h2-apt-utility4-inplace-runtime-probe/run-002/runtime/offline-gate-attestation.json.

The first attempt in run-001 failed before a guest breakpoint because the long staged profile path exceeded a Windows path limit while Azahar created a system config directory. Its logs and profiles are preserved. The runner was changed to launch through verified 8.3 aliases; the fresh run-002 succeeded.

## Limits

- The probe stops at the original wrapper entry before its body and APT service call. It does not capture the wrapper result, SVC response, service side effects or caller continuation.
- Only the observed ARM route is exercised. Indirect, computed, mixed-state and out-of-range callers are not ruled out.
- The broader TitleConfig runner separately failed after the original scenario because Azahar did not exit within 15 seconds after WM_CLOSE; it stopped before running the patched profile. That failure remains recorded under build/agent-work/H2-semantic/h2-apt-utility4-inplace-runtime/run-001/.
- H2 TitleConfig remains open; this probe neither closes H2 nor changes the source ledger.
- The base manifest retains four source_identity_mismatches; the package review documents them.
