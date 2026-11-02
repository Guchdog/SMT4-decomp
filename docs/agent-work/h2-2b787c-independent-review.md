# Independent review: `0x002B787C` line-count candidate and staged image

## Review decision

The candidate is suitable to proceed to a **bounded autonomous runtime comparison**, provided the selected scenario is confirmed to execute `0x002B787C` and captures its return/use. The offline implementation, final-address differential, patch construction, and compile artifacts are internally consistent. I found no implementation counterexample in the reviewed control-code or signed-bound paths.

Do **not** treat this review as runtime approval or commit/push approval. Runtime is still `not_run`; the two other direct callers are statically mapped only. Before commit/push, close the runtime comparison and coordinator integration review. Also strengthen the signed-bound negative control described below before using the six-control claim as a final promotion gate. A runtime scenario aimed at the H2 callback path should not be assumed to hit this dependency: the documented callback passes selector 6, whereas `0x00286928` calls `0x002B787C` only for normalized selectors 11/19.

## Frozen input and artifact identity

All `input_sha256` entries declared by the independent-review packet matched the current checkout at review time, including the candidate, production source, contract, reports, runner and patch scripts. Reference `code.bin` matches the pinned SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

The candidate and production implementations are separate compiled artifacts: the standalone candidate body is 176 bytes with SHA-256 `a0598cb09e2d4c3f288bb87b3470b90e47d88ed7d129f271d8a344a92c4a88e5`; the staged production body is also 176 bytes but has SHA-256 `1f2cd6d6f0487f9c6cb12ce3f2363a19513c13969ac5b96df4d0e6b6e0cc08fe`. The final-address report explicitly tests the production body in the staged image, so the body-hash difference is not hidden by relying only on the standalone candidate result. The ledger row is `non_matching`, correctly reflecting the changed bytes.

I independently checked staged artifact hashes against its manifest: patched image `a915d0baee331366636fd9e25d55bfafa3554351f15d242fce3f52f9675d1dec`; IPS `a501c4b078961d69ac720f252331f29380d4186dfebe1ec333902891e57896c2`. The staged image has the pinned original length, changes zero bytes outside the function slot, and the body is exactly 176 bytes. Decoding the two relocated ARM `BL` instructions gives targets `0x002AE6B0` (offset 68) and `0x002AE664` (offset 112), both even ARM-state addresses. The IPS is one record and its manifest reports a successful round trip. No interworking or slot-boundary contradiction was found.

The full-build directory contains 204 object files, 204 metadata files and 204 dependency files. The `leaf_batch42_c.o.json` metadata pins the current production source SHA-256 and object hash `cc21cde4b80d87df50f8952055aa3c6a9920a9bb9da441be5a8092f1d44d69b9`, matching the staged manifest. I did not find a retained full-build stdout/summary file in the declared path, so the 204/204 exit-success claim is supported by the implementation report and complete build artifacts, not an independently inspected console transcript.

## Contract and implementation review

The C++ follows the pinned ARM algorithm on the reviewed paths:

- Gate `handle+0x14`; zero returns zero.
- 32-byte records and `0xFFFF` end marker.
- Retained `0x002AE6B0` predicate for unsigned `0xF801..0xF88F`.
- `0xF801` increments count; `0xF802` returns it; `0xF81A` loads the next halfword as the new count and advances past it.
- Other recognized codes call retained `0x002AE664`; its word return is an index delta.
- The post-advance bound is signed. Candidate exit condition `signed(index) >= signed_limit` is the complement of original signed `limit > index`, for the same stable `handle+0x0C` value.

The original reloads `handle+0x0C` in the loop; the candidate caches it in `start`. Neither retained direct callee writes the handle, and the function has no local handle writes, so this is equivalent for stable ordinary memory. Concurrent mutation of the handle/bound is explicitly outside the stated evidence domain. The raw pointer/handle validity and valid sentinel/mapping-table assumptions remain material limits.

## Differential, caller, and negative-control evidence

The offline report is internally consistent with the runner source:

- **515 direct cases:** 12 directed seed cases, 420 mapped recognized-code cases (140 non-special recognized values × deltas 0/1/3), three outside-range cases, and 80 seeded cases (40 each for seeds 4729 and 20261102).
- The matrix exercises all non-special codes in the recognized range, the three special codes, mapped/unmapped controls, count/stop/payload behavior, and both sentinel and signed-bound termination. Original `0x002AE6B0` and `0x002AE664` execute from the pinned image. Return/fault, callee-saved registers, SP, VFP callee-saved registers, direct-callee order/arguments/returns and the stated memory regions are compared; no non-stack guest writes are expected.
- **Two caller compositions:** original `0x00286928`, selectors 11 and 19, with controlled fixture state and deterministic hooks for its other dependencies. Both enter the line-count routine and consume return value 2 at `object+0x20`. These are useful focused compositions, not complete original-dependency executions or evidence of runtime selector distribution.
- **Six mutation controls:** sentinel, count control, stop control, payload control, mapped delta, and signed bound all report detected. Each source mutation is anchored uniquely and the runner checks that compiled mutant bytes differ from the good body.

One control-quality limitation: the signed-bound mutation case uses `start=0x7FFFFC20` with fixed `RECORDS=0x00920000`. The shifted/wrapped record address lands at `0x00118400` inside the mapped original code image; later records traversed by the unsigned-bound mutant are therefore not a separately initialized line table. The check does detect a difference on this pinned-image-backed fixture, but it does not isolate the comparator using controlled ordinary table contents. Before treating that control as strong promotion evidence, choose a table base whose wrapped target lands in a separate initialized mapped region (or otherwise initialize and assert the traversed records), then rerun the focused evidence.

The 286928 compositions cover raw selectors 11 and 19. Raw 13/14/15 normalize to selector 11 and use the same pointer-table slot, but their selector-specific prewrites differ. Their parent composition is not covered. This is not a counterexample to `0x002B787C` itself, and it does not block a runtime probe explicitly limited to selectors 11/19; it limits any broader claim about all parent selector routes.

## Runtime and commit/push recommendation

Proceed with an autonomous original-versus-staged runtime comparison only after choosing a real caller scenario and verifying a breakpoint/hit at `0x002B787C`. Compare the raw helper return and the caller-visible use (for example the `StatusDown_UpdateHelpMessage` list-count setup); record the exact scenario, staged image/IPS hashes, entry arguments, return, and relevant caller state. The H2 callback scenario by itself is not evidence for this helper because its known selector is 6 and that route does not call the line counter.

Do not commit/push the reconstruction as a promoted replacement yet. First close that scoped runtime comparison, resolve or document the signed-bound-control fixture weakness, and let the coordinator review the final artifacts. Keep the remaining input, alias, table-termination and runtime-distribution limits in the record; this does not establish all callers, arbitrary malformed tables, or whole-game/H2 equivalence.

## Commands and evidence levels

Read-only review actions used (no compiler, runner, build, or emulator command was run by this reviewer):

- Read packet-declared inputs and recomputed SHA-256 values for the packet's frozen files.
- Read the implementation, candidate, contract, runner, patcher, staged validator, offline reports, manifest, ledger row and build metadata.
- Parsed manifest/staged image/IPS bytes to check image hashes, changed-byte range, function slot size, and the two relocated branch destinations.
- Counted the full-build `.o`, `.o.json`, and `.o.d` artifacts: 204 each; checked production TU source/object metadata.

Evidence status after this review: compiled `passed` (reported and supported by object artifacts); ARM differential `passed` for the recorded 515 cases; caller `partial` (two synthetic-service compositions through one caller; two other callers not executed); runtime `not_run`.

## Follow-up addendum — run002 (2026-11-02)

I reviewed the revised run002 packet and recomputed every declared input hash; all match. The conversion report is run003 (`e7265603d4ba074c55c002148ce85981f01e25b08a2cfaa79f726e0a8e366f1f`), while the staged manifest, staged-validation report, production source, candidate, patch tools, and pinned image remain at the frozen hashes declared by the packet.

The **direct** `signed-bound-wrap` case is now correctly isolated. With `start=0x7FFFFC20`, `(start << 5) mod 2^32 = 0xFFFF8400`; `table_base=0x00927C00` therefore makes the wrapped first-record address `0x00920000`. Record offset 1 is at `0x00920020`, and offset 998 is at `0x00927CC0`. The full initialized record allocation ends at `0x00927D00`, within the fixture's `0x00900000..0x0095FFFF` mapping and separate from the loaded code image. The direct case seeds offset 1 with `0xF801` and offset 998 with `0xFFFF`; offset 0 remains the initialized ordinary value. Original signed bound is `0x80000007` interpreted as `-2147483641`; after offset 0, index `0x7FFFFC21` is positive, so original signed `limit > index` is false and it exits with count zero. This is an appropriate controlled direct boundary comparison.

The **negative-control mutation case is still not fixed**. In `negative_controls()`, `nc-bound` is constructed as `Case("nc-bound", start=0x7FFFFC20, writes=((0, 0x0041),))` and omits `table_base`. It therefore retains the default `RECORDS=0x00920000`, which wraps the first record to `0x00118400` inside the loaded code image; it also does not install the offset-998 sentinel reported for the direct case. The report's `signed_bound_control_fixture` describes the corrected direct `signed-bound-wrap` case, not the separate `nc-bound` passed to the mutation comparison. Thus the new direct fixture resolves the prior boundary-fixture concern, but the claimed signed-bound negative-control detection still depends on uninitialized code-image contents. Propagate the table-base override and controlled record pattern/sentinel into `nc-bound` and rerun that control before relying on all six controls as final evidence.

**Updated recommendation:** the direct original-vs-candidate bound evidence is strengthened, and no new candidate mismatch was found. Proceed to the bounded autonomous runtime comparison if the scenario confirms an entry at `0x002B787C` and compares its caller-visible result. Keep the negative-control issue open before commit/push; it does not block a scoped runtime probe. Runtime remains `not_run`, and the known H2 callback selector 6 still does not take the `0x00286928` line-counter route.

## Follow-up addendum — run003 (2026-11-02)

All run003 packet input hashes matched the frozen values, including the updated runner and offline report (`3e56cf5936abf139c2ce29e0c9b9b6a897419a638a1de3a47cf99bb601dc50e1`). The staged manifest and final-address validation report remain pinned to the same hashes reviewed above.

The signed-bound fixture caveat is **resolved for both the direct case and the negative control**. The runner now supplies the same computed `table_base = 0x00927C00` to `signed-bound-wrap` and `nc-bound`. With `start=0x7FFFFC20`, the wrapped first record is `0x00920000`; offset 1 is `0x00920020`; offset 998 is `0x00927CC0`. The initialized table allocation spans `0x00920000..0x00927CFF`, within the mapped `0x00900000..0x0095FFFF` data region. Both cases set record 0 to ordinary `0x0041`, record 1 to `0xF801`, and record 998 to `0xFFFF`.

For the original signed test, `start+0x3E7` wraps to `0x80000007` (signed `-2147483641`); after the first ordinary record, the index is `0x7FFFFC21` (signed positive), so the signed `limit > index` loop condition is false and the helper returns count 0. The unsigned-comparison mutant instead continues: it consumes the `F801` at offset 1, increments count to 1, then reaches the initialized sentinel at offset 998 and returns 1. This isolates the intended comparison difference without reading table records from the code image.

The revised offline report retains **515/515 direct cases**, two selector 11/19 compositions, and all six controls marked detected: sentinel, count, stop, payload, mapped delta, and signed bound. This reviewer did not run the runner; the assessment comes from the frozen source and report, plus independent address arithmetic. Other offline/staged/204-TU evidence remains as described in the prior review. Caller/runtime coverage is unchanged.

**Updated recommendation:** the signed-bound control caveat is resolved. Proceed to a bounded autonomous original-versus-staged runtime comparison that confirms an actual `0x002B787C` entry and checks its caller-visible result. Keep commit/push pending that runtime result and coordinator integration review. Do not use the known H2 callback selector-6 route as evidence that this helper executed; the helper call in `0x00286928` is gated by normalized selectors 11/19. Runtime and whole-game equivalence remain unestablished.
