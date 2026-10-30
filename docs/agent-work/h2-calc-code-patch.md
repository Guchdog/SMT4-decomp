# H2 Calc code-cave patch experiment

Status: experimental patch construction and final-address ARM differential passed. This is not production promotion or H2 runtime acceptance.

## Artifact

`tools/h2_calc_code_patch.py` compiles the reviewed `TitleConfig_Calc` candidate, checks the pinned `code.bin` identity/layout and unused cave, applies its four audited local `R_ARM_ABS32` relocations at cave VMA `0x003FE624`, and branches from entry `0x001EA928`. It emits `code.experimental.bin`, `code.ips`, and a manifest under ignored `build/` output. The builder independently applies the IPS and verifies that bytes outside the branch word and candidate blob remain identical.

Run outputs:

- `build/agent-work/H2-semantic/h2-calc-wrap-semantics/run-001/checks/patch-seed-7`
- `build/agent-work/H2-semantic/h2-calc-wrap-semantics/run-001/checks/patch-seed-20261024`

Both runs produced identical patched-image and IPS hashes:

- Original `code.bin`: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Patched image: `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`
- IPS: `0b671f4f40c172984e730d0387899ce47abe8f2ee5e90043a2e481aa591cf781`
- Candidate source: `16f2af7c953a089ffe277d2f299ea89ab90d028f57d6708ffdc8cf6115844ed2`
- Candidate object: `cd4c0eb1cbf21ac849f994370c0403fb2a6919b0263afd834db5928e768c60b`

The source now uses defined `u32` subtraction and multiplication for the special
handle arguments. This compiler emitted the same 2,096-byte ARM body and object
hash as the prior candidate, so the patched image and IPS hashes are unchanged;
the source hash changed and is recorded separately in each fresh run report.

The 2,096-byte body fits the 2,524-byte cave. The entry branch bytes are `3d4f08ea`. Relocations at body offsets 60, 64, 68, and 72 resolve respectively to `0x003FE670`, `0x003FE7E4`, `0x003FE790`, and `0x003FE7C8`.

## Checks and result

- `python -m py_compile tools/h2_calc_experiment.py tests/test_h2_calc_experiment.py tools/h2_calc_code_patch.py tests/test_h2_calc_code_patch.py` — passed.
- `python -m unittest tests.test_h2_calc_experiment tests.test_h2_calc_code_patch -v` — 9 tests passed; includes four directed special-handle arithmetic boundary scenarios and expected modulo helper words.
- The fresh patch builder compiled the candidate for both seeds with exit 0.
- Final-address differential, seed 7, 32 random samples plus 36 directed cases — 68/68 cases passed.
- Final-address differential, seed 20261024, 32 random samples plus 36 directed cases — 68/68 cases passed.
- Wrong-branch negative control (`cave + 4`) — detected in both runs; callback failed to reach the return sentinel.

## Evidence limits

The differential compares the pinned original ARM callback with the patched-image callback at its final guest VMA under identical explicit service mocks. This supports the patch placement and the candidate's tested behavior at those boundaries. It does not cover original caller composition, unresolved helper internals, real input, the H2 edit/cancel/confirm sequence, persistence, Azahar runtime, or restart behavior. The negative control checks branch redirection; it does not separately perturb each relocation.

The special-handle difference and scaled arguments now use defined modulo-u32 operations. Directed original-vs-patched cases cover extreme signed helper returns and compare exact helper argument words. This establishes the arithmetic translation over the tested s32 input bit patterns at the mocked helper boundary; it does not establish the real script-helper domain or `bounded_value` semantics.

No production C++ or ledger entry was changed. The source remains experimental, and the production ledger must not classify differing bytes as `matching`.
