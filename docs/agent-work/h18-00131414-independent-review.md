# Independent review: paired store at `0x00131414`

## Verdict

The isolated machine candidate is strongly supported for the tested contract: on aligned, writable ordinary RAM, store `r1`/`r2` to `p+4`/`p+8` in order and return `p+4` in `r0`. Do not promote the current typed C++ definition unchanged. Its invented `PairStoreRecord` argument/return types do not match the production declaration or establish the real caller object's C++ type. Resolve and encode the caller layout in a source-level contract first.

## Original, candidate and return behavior

The pinned original image hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. At `0x00131414` the exact 12 bytes are `040080e2060080e81eff2fe1`, decoding to `add r0,r0,#4; stm r0,{r1,r2}; bx lr`. The original's return is the adjusted pointer `p+4`, not void. The batch-002 candidate compiles to 12 bytes at patch destination `0x003fe6d0`: `stmib r0,{r1,r2}; add r0,r0,#4; bx lr`. This stores at the same addresses and returns the same pointer, but has different bytes and changes when r0 is adjusted relative to the stores. No byte-identity claim is appropriate.

The experiment candidate in `experiments/semantic_equivalence/candidates.cpp` uses a test-only `PairStoreRecord { prefix, first, second }`, stores `first` and `second`, and returns a `PairStoreRecord*` formed from `record+4`. This correctly models the observed register value at the ABI level, but the returned type is misleading: a pointer to the interior `first` word is not evidence of a `PairStoreRecord` object there, and dereferencing it as such would not be justified. The current production declaration and inline-assembly definition are both `void ui_func_00131414(u8*,u32,u32)`. A typed non-void definition cannot be dropped under that declaration without reconciling the declarations. The test record is not a recovered game type.

## Differential and caller evidence

The direct evidence for this address is in the two `batch-002-callers` reports, not in the separate `paired_store_experiment.py` reports. Batch-002 tested `0x00131414` against the candidate source/object hashes `866849a516c276e00cb447c1c1d557f2f9952672fac8f8026cc3af3b14054699` / `ef053a4af5616a171e64e9a12c1d1e0876f97fcb9005543babbd0301ba5adcd7`. Both seeds passed 4,107 differential cases for this leaf, with the candidate disassembly above. The wrong-pair-store negative control was detected on its first case. The seed-7 and seed-20261024 reports hash to `a75cea2e2f1af34040c4963712dea76882f7f1827355471461049550caef0780` and `ca85a82426f149d497d1d7e090da95818f799af9df9297fa0aea7751e61453b9`.

The narrow caller window at the real callsite `0x00121d1c` passed 267 cases per seed and continued at `0x00121d24`. The caller loads `r0` from its saved `info`, places `resource` in `r1` and `found` in `r2`, calls the leaf, then executes `mov r0,#1`; it therefore discards the leaf's `p+4` result. That is concrete evidence the known caller does not consume the return. It does not make the leaf return void, nor does the narrow window execute the parser path that produced `resource` and `found`.

The separate `paired_store_experiment.py` reports hash to `f1777c917ecb42f224047374c1abcc11a2f374182cb11ac0f883a0632b2cef20`, `e7c2a67e56b2a760f71647232c9025a424ee63dc276eb3f667d4edc08517486e`, and `dbf1e3c51e57e2964f4749ecd6cabbb6fe8f82ebbb98c36f8c613a11817ac863`. They compile a different TU (`paired_store_candidates.cpp`) and different store offsets (`+0x84`/`+0x40`). For `0x00131414` they verify the original bytes and direct-caller inventory, but do not test the `candidate_00131414` body. Their pass flag must not be cited as differential proof for this address.

Caller inventory records exactly one direct ARM BL site, `0x00121d1c`. The parser function record identifies the writes as `info+4 = resource` and `info+8 = found`; `info+4` is also checked on entry. This identifies the observed layout and call arguments, but does not establish a named C++ state type, its object lifetime/aliasing model, or execution through the real game loader. Caller-window comparisons cover writes and continuation, not the whole parser behavior or actual asset-loading scenario.

## Type, ABI and integration requirements

At the ABI boundary all three integer arguments arrive in `r0-r2`, and the pointer result is returned in `r0`. The known caller ignores it. For source integration:

1. Recover or define the actual state type from the parser's `info` object, and assert the fields at `+4` and `+8` and the required alignment/extent.
2. Give the function one consistent declaration and definition. If the helper is intentionally opaque, return a pointer type that truthfully represents `p+4` (for example a byte pointer); do not claim it returns a `PairStoreRecord*` unless that is the actual object type.
3. Ensure the C++ stores are valid for the caller's real object type and memory domain. `PairStoreRecord` dereferences assume a live suitably aligned object of that type; this test scaffold alone does not prove strict-aliasing/object-lifetime safety for the actual `AsdFontParseState` storage. Retain the documented ordinary-RAM domain; MMIO/volatile observers, unaligned addresses, concurrent observation, exceptions and partial-fault ordering were not tested.
4. Keep the ledger truthful. Current production remains the exact `matching` original. If the non-identical C++ body is promoted, classify it as supported non-matching and retain a semantic record; the generated 12-byte replacement differs despite its size matching.
5. Before integration closure, run the relevant production/caller-composition regression with the reconciled typed interface, then the defined patched runtime scenario if required. Existing seed reports and the 267-case window are not whole-parser, asset-loader, or full-game runtime proof.

The historical test patch redirected the entry to `0x003fe6d0` (file offset `3139280`), generated IPS hash `5d0cb36fa319678872d7c96ce9a9f878a6df393dbe5b6c3847702c2df749a89a`, and patched-image hash `3b4595c91b1ad41457cab8dc6f4196fadb7ae47c045a828b46adf80120295116`. These are ignored experimental artifacts, not a production integration or loader test.
