# Independent review: `0x002AE664` ASD map helper

## Decision

The C++ body is a plausible bounded reconstruction of the pinned lookup helper: it preserves sentinel-before-match ordering, returns the first matching row’s `u32` payload, and returns zero when the sentinel arrives first. The test design covers the full halfword key domain plus sampled wider inputs and representative table layouts. Keep the function `non_matching`.

I do **not** recommend accepting run001’s report/cumulative-composition evidence as finalized until two provenance defects are corrected: `report.json` is not strict JSON because it ends in a literal `\\n`, and the cumulative runner recompiles `0x002AE6B0` without recording that body/source hash in this report. These do not reveal a functional counterexample in the `0x002AE664` implementation. The helper’s direct semantic result is strongly supported by the report contents, but promotion based on the full two-helper cumulative claim should wait for a report that is machine-readable and pins both installed helper bodies.

## Pinned contract and ABI

All 18 packet-declared input hashes match. The pinned code image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The 76-byte original function slice hash is `9a08149396d2a69f6c46775ebffc83c59cdd30f2d1fc9fa8cdcb04a121106f56`; Capstone decoding confirms:

- Entry `r0` is compared as a raw 32-bit value against zero-extended table `u16` keys.
- The table address is loaded from an in-slot literal as `0x00464DA8`; row stride is 16 bytes, key offset 0, result offset `+4`.
- Each row checks `key == 0xF890` **before** comparing the key with input. Sentinel first returns zero; a prior match returns the row’s 32-bit payload; the first duplicate wins.
- Original caller code stores `r4` at `[sp-4]` with predecrement, then restores it and SP at return. The pinned table itself contains its sentinel at row 16 (`0x00464EA8`), supporting termination for the original initialized table.

The C++ loop uses the same row layout and comparison order. A `u16` key promotes without sign extension when compared with `u32 code`, so values above `0xFFFF` cannot match. Such inputs still terminate at a readable sentinel and return zero. The function has no explicit bound or null/sentinel check; unreadable tables, missing sentinels, concurrent mutation, or mapped-memory side effects are outside the supported domain.

The candidate body reported is 56 bytes, SHA-256 `0d4f0c8ea3c90c3827b5e155135d9d85be27624833a9e4aec53fa5629a48e2aa`, with no relocations, inside the original 76-byte span. The decoded candidate loads a literal pointer to `0x00464DAC` (the key-plus-four cursor), compares the key at cursor minus four against sentinel and input, and loads the result at the cursor. The body differs from original bytes, correctly requiring the `non_matching` ledger class.

### Stack spill qualification

The pinned original intentionally spills `r4` to `SP-4` and restores SP; the C++ candidate uses no stack. The runner records stack writes separately, compares SP and `r4-r11`, and excludes only `[STACK-4, STACK)` from the non-stack-write equality check. That is a reasonable normal AAPCS call model because the callee allocates that spill slot below entry SP. It is not byte-for-byte equality of stack scratch memory; callers relying on data below their current SP are outside this ABI claim. The report accurately calls out this distinction.

## Direct differential and controls

The runner builds a 256-row, 16-byte-stride fixture with a sentinel at the first unused row. It checks 65,536 halfword inputs exhaustively, six directed 32-bit values (including `0x10000`, signed-boundary values, and high values), and 256 deterministic samples from seed `20261103`. Those sets yield the reported 65,798 distinct direct calls. The default rows include duplicates for `0xF803`; the oracle walks forward and stops at the sentinel, so first-match behavior is checked. Additional layouts cover sentinel-first, a match at row 31 before the sentinel, and duplicate-first-wins. Every result is checked against a separately written table-walk oracle.

Two source mutations are targeted and detected:

- Shifting the key comparison to `key == code + 1` changes input `0xF802` from no match (0) to the later `0xF803` payload (3).
- Moving the sentinel to `0xF891` allows input `0xF890` to match the sentinel row’s deliberately nonzero payload `0xDEADBEEF`; the original correctly returns zero.

The direct comparator checks result, `r4-r11`, SP, external writes, fault status, and completion. It deliberately does not require identical stack-spill traces, as qualified above. I did not run the compiler or differential.

## Cumulative caller composition

`run_compositions()` patches the map candidate into the original image, fills the rest of the 76-byte slot with ARM NOPs, and also patches in a compiled `0x002AE6B0` predicate body. It compares original `0x002B787C` across all 515 line-count fixtures and original `0x00286928` for selectors 11 and 19; the parent outcomes consume line count 2 at `object+0x20`. The report says all comparisons matched. The line-count and dispatcher harnesses use deterministic hooks for other dispatcher services; this is useful controlled composition, not runtime reachability or complete service execution.

The runner report embeds hashes of `h2_2b787c_experiment.py`, `h2_86928_experiment.py`, and `h2_ae6b0_experiment.py`, and the packet pins those harnesses. However, `h2_ae664_experiment.py` calls `control_predicate.compile_candidate()`, which compiles the current `src/engine/leaf_matching.cpp`; neither that source hash nor the predicate candidate body hash is included in the map report or packet. The current predicate source SHA is `2a59d7aeba7fa2f9f70046b2e9dea87a2e65471a0069886e3b84e1ce2daf58d3`, matching the separate predicate report, whose body SHA is `d6476e69b5213740930513337c57f5caec10b08cb9d54e59fc6c51e485332d58`. This supports that the present inputs agree, but run001 does not prove those exact values were the cumulative image’s values at generation time. Record the body/source hashes directly in a fresh composition report to close that gap.

## Report integrity finding

`build/agent-work/H2-semantic/h2-ae664-convert/run001/report.json` has the expected report hash from the packet, but its final bytes are `}\n` (literal backslash and `n`, following the JSON object), not JSON whitespace. `json.loads()` raises `Extra data` at the trailing backslash. Removing those two final bytes allows the contents to parse and confirms the displayed `body_hex` matches the reported candidate SHA and 56-byte length. The runner source writes `+'\\n'`, which produces this invalid trailer. Regenerate or normalize the report with a real newline, update its hash and downstream function-record pin, then rerun `check-handoff` for the implementation packet if that report is a referenced deliverable. No content-level counterexample was found after parsing the object body.

## Evidence status and next action

- Compiled C++: **passed by read-only object extraction**. The existing `leaf_batch28_b.o` is 18,004 bytes; its extracted `func_002ae664` body is 56 bytes, SHA-256 `0d4f0c8ea3c90c3827b5e155135d9d85be27624833a9e4aec53fa5629a48e2aa`, with no relocations. This reviewer did not compile.
- ARM differential: **partial pending report repair**. The runner logic and embedded data support the 65,798 cases and mutations, but the artifact named `report.json` is invalid strict JSON.
- Caller composition: **partial**. Two selector compositions and 515 original line-count cases are reported; unrelated services are stubbed, and the second helper’s exact compiled body is not bound into this report.
- Runtime: **not run**. Natural runtime frequency/reachability and full H2 acceptance are not claimed.

Recommendation: preserve the semantic implementation and `non_matching` ledger class, but repair the trailing JSON escape and bind the `0x002AE6B0` source/body hash into a fresh cumulative composition report before treating this packet as a final promotion/acceptance record. Leave malformed/sentinelless table inputs and runtime caller coverage explicitly outside the claim.

## Review actions

- Recomputed all 18 declared packet input hashes and hashes of the original function span, report candidate bytes, and the existing candidate object’s extracted function body.
- Decoded the pinned function and reported candidate bytes without compiling; inspected table sentinel placement and runner’s fixture, oracle, observation, negative-control and composition code.
- Parsed the report after removing its invalid literal trailer to inspect its fields; strict JSON parsing fails on the unmodified file.
- No compiler, build, test runner, or emulator was run.

## Follow-up addendum — run002 (2026-11-02)

All 20 run002 packet input hashes match. This packet now explicitly pins `src/engine/leaf_matching.cpp`, its header, and all imported composition harnesses (`h2_2b787c_experiment.py`, `h2_86928_experiment.py`, and `h2_ae6b0_experiment.py`). The corrected report parses with strict `json.loads()`; its final bytes are ordinary CRLF/JSON whitespace, not the prior literal backslash-n trailer. The updated report SHA-256 is `b6ecbe958f0ec299a4366fe64f2a503b643ab74295407cfd2a2cedf3e1516e60`.

The report’s `caller_composition.integrated_helpers["0x002AE6B0"]` now binds source SHA `2a59d7aeba7fa2f9f70046b2e9dea87a2e65471a0069886e3b84e1ce2daf58d3`, compiled body SHA `d6476e69b5213740930513337c57f5caec10b08cb9d54e59fc6c51e485332d58`, and 24-byte body size. Those identities match the newly pinned predicate source and its separate conversion report. The map helper’s own 56-byte body SHA, zero-relocation claim, 65,798 direct cases, three table layouts, two controls, 515 line-count compositions, and selector 11/19 parent compositions remain as previously reviewed. The existing map object still extracts to the same body hash without relocations; no build was run.

The run001 report-format and second-helper-provenance gaps are resolved. No new counterexample was found. **Updated recommendation:** accept the bounded table-map reconstruction and cumulative offline composition with both helpers converted; preserve `non_matching` status and the documented readable-sentinel/table-domain, original stack-spill, deterministic-service-hook, and not-run runtime limits. No natural reachability, runtime frequency, or full H2 acceptance is established.

Run002 actions were read-only packet/report hash checks, strict JSON parsing and body/source identity comparison, plus source and composition inspection. No compiler, build, runner, test, or emulator was invoked.
