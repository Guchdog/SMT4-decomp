# H2 live binary pin sync — run-001

Updated the private live preflight executable pin from the superseded hash to the reviewed binary SHA-256 `1bec8c3fef5b794e0abfe4bbbc1870202c562bb35ef3e49648b1d09060f8e6f1`. Updated the production-artifact pin assertion in the focused fixture. The wrong-private-binary test remains intact and verifies mismatch rejection before subprocess launch.

Regenerated `h2-delivery-manifest.json` from the private package. Its binary entry matches the reviewed executable; the regenerated manifest hash is `b7ee31e1675444036f0efb03f579d63c0f95425399451329685655f4df10f147`. Independent package verification passed all 30 entries across the binary, feature inputs, compatibility shim inputs, and patch artifacts.

The focused live-preflight suite passed 19/19. Read-only `preflight_h2_live()` calls succeeded for both staged run-012 profiles. Both plans pin the same staging manifest (`4cf56358d3a0548adfdb85894fb4204903bb6364645e1afc30ff398f306dd7d7`), original H2 image (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), final H2 image (`acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446`), integration manifest (`577c89588e031dc3eb1878d474cade85d5fe62f1f41c27816c4d7e92cd304d27`), CCI (`9cc760c2f37da9a4a3657e918e0eaebb3e8e80a91047e5c18f95aedf0242b4c2`), standalone IPS (`67e4758255fe1f4bc5877e2c997ae931613e631a5a11d487cea0e095ff630beb`), and staged executable (`c248414eb5328cb8bb720775ace6959898e2f50a0a10221c3a1e7a14190183eb`). The selected profile inventory hashes differ as expected: original `f1af6d4ecefd20d46546c8e1ade8cd26482b7218fbd4b9aac92e9ff921d65b18`; patched `b934c2efb948b4051c969c28657391269447635301447d4d3bf43f835ad5cc84`.

Fresh output paths were reserved but not created: `E:\SMT4decomp\build\h2-manual-comparison\run-012\live-pin-sync-original-20261027.jsonl` and `...\live-pin-sync-patched-20261027.jsonl`. No emulator process was launched; no profiles were modified. This establishes preflight readiness only, not runtime behavior or H2 equivalence. No build was run.

## Evidence and checks

- `python -m unittest test_h2_live_preflight -v` — passed, 19 tests.
- `python <run-001>/checks/verify_package.py` — passed, 30 package hash entries.
- `python <run-001>/checks/preflight_profiles.py` — both profile preflights returned `ok: true`; detailed output is in `reports/preflight-results.json`.
- No Azahar launch, build, debugger, RPC, or input automation.

Next: independent review of the pin change and package manifest, then coordinator may use the guarded live wrapper if separately authorized.
