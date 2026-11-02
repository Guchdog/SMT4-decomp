# Independent review: cursor range wrapper `0x0029EDFC` — run001

## Recommendation

The frozen run001 evidence supports the bounded typed reconstruction of `0x0029EDFC`, with original `0x002892C0` retained as an explicit dependency. The candidate and production wrapper bodies are identical after final-VMA relocation (44 bytes in an 80-byte slot), and the one `R_ARM_JUMP24` targets the even ARM entry `0x002892C0`. The 14-case direct matrix and three controls cover the stated wrapper contract and selected helper boundaries. Four caller compositions exercise the actual original `TitleConfig_Calc` touch path for indices 0, 1 and 2, plus the selected-row skip.

The recorded caller comparison is explicitly original `TitleConfig_Calc` versus that same pinned original image with only this wrapper slot patched. The cumulative IPS is a separate staging artifact. Evidence supports proceeding with bounded semantic integration/review, not claiming full runtime or whole-game equivalence.

## Provenance and patch

All 30 run001 `input_sha256` entries recompute exactly. Key identities:

- Pinned image: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
- Candidate source: `c870588706dd7e767e86af7f50beaf50972c609dd236ee86b41f6c15cd0ad5c3`
- Candidate object: `402b9f73e65bd4c78d4a0e54e8bef4c53c44a0df0233d6f80b73d23ea2b289ef`
- Production object: `4f8b460b752a2418b0537489f3bf80d0b05deb2dcf1c216b5f3a480795b40443`
- Tail-helper object: `e8cfa20c7043b0a04c277088c2e73bf9c7b4755495dec55e9feb31a88033b2af`
- Report / staged manifest: `cde92c34c5feaae81144e6f8d0ebf1d736fed1245a48a5383538352a42a27b1d` / `52a78795cb879abb214b0ad4a0ad1b2009e251eacc6760303c8c5502b8ba6daa`

Candidate and production body hashes are both `1e9def2352c4da55d3a1dc80b1fbf0debd06ca14cf987d8315fc17a54476f9af`, 44 bytes each. The only relocation is `R_ARM_JUMP24` at body offset 40, resolved to `0x002892C0`; the target address is even, so it enters ARM state. The original helper body is 124 bytes and its source/object metadata SHA agrees with `build/h2-0029edfc-full/engine/leaf_batch16_c.o`.

Staged image SHA-256 is `a865c64d96785558c1d204b6aa89a3f97369b2b1f27f76d8beb5e3b543c9e25b`; IPS SHA-256 is `f5d6024ae155316ae795a6621ef4bf5a348c23d873a386f985347322f6a8da6c`. Manifest and report agree on 76 changed bytes, slot `0x0029EDFC` size 80, slot-only changes and successful IPS roundtrip. The row in `config/functions.csv` truthfully classifies the differing implementation as `non_matching`.

## Contract, helper dependency and ABI

The C++ wrapper accepts `(void* object, u32 index)` and reads the raw byte at `object+0x62`. If nonzero it returns that byte unchanged without helper call or object write. Otherwise it reads `u32` at `+0x24` and `+0x20`, compares their modulo-2^32 sum with the original full-width index, and stores byte 1 at `+0x60` only on mismatch. Equal sums preserve the previous flag byte. It tail-calls `camp_func_002892c0(object,index)` and propagates its return.

The declared helper ABI is `(void*, u32) -> u32`, consistent with the existing ARM body and caller register use. The original helper is retained, not reimplemented: its pinned body uses signed ARM comparisons for count/index and delta bounds, writes cursor words at `+0x20/+0x24`, and returns 1 in the exercised normal paths. The wrapper makes no null check; a valid object and mapped words/bytes are required. No validity guarantee is established for arbitrary count/visible values or malformed objects.

The direct report compares returns, mapped object state and ordered non-stack writes, call count/arguments, final SP, callee-saved registers and VFP preservation. It explicitly records four original stack save writes versus zero candidate stack writes; the original restores them before return, and the harness checks final SP and preserved state. Thus the temporary caller-stack spill pattern differs, while the tested caller-visible post-return ABI/state matches. Do not treat transient stack-write identity as established.

## Direct cases and controls

All 14 cases pass against the pinned original wrapper plus original helper. They cover disabled returns `1`, `0x80`, `0xFF`; equal sum with a preexisting flag; mismatch setting the flag; modulo wrap; zero count; zero and negative indices; `count-1`, `count`, `count+1`; visible count above configured count; and a high positive signed boundary. The report preserves helper ordered-write sequences, including the successive `+0x24` updates and final `+0x20` store at `index-count-plus-one`, and the two zero stores on the helper's zero-count path.

All three compiled controls are detected: normalizing the disabled byte return, inverting the flag condition, and changing the helper index by one. These are useful mutation checks but do not enumerate every signed-overflow/malformed-object edge or establish helper behavior beyond the retained original implementation and exercised fixtures.

## Original caller composition and build evidence

The harness constructs `final_image` from the pinned original `image` and replaces only the `0x0029EDFC` slot before invoking `CursorCallerMachine`; this keeps original `TitleConfig_Calc` and its call at `0x001EAEA4`. Three scripted touches reach the wrapper and tail helper with handled indices 0, 1 and 2. The fourth case touches the selected row and confirms both wrapper and helper are skipped. Each compares return, state, trace and ABI between original and patched runs. Touch service results are controlled (`6`), so physical input and timing are not exercised.

The supplied full-build object tree contains 204 `.o` files and 204 matching `.o.json` metadata files. The five packet-pinned dependent objects exist and their hashes match; in particular the rebuilt wrapper object matches the run001 production object and the original tail-helper object matches the full-build leaf object. This corroborates the reported 204/204 full ARMv6K build artifacts. I did not run the build, so this review does not independently validate its command exit or rebuild freshness beyond the frozen dependency metadata/hashes.

## Limits and next step

Runtime is `not_run`. The controlled fixtures do not establish physical touch production/timing, scheduler behavior, arbitrary pointer safety, concurrency, full object invariants, every original caller's value domain, or whole-game equivalence. Proceed with bounded semantic integration, keeping `0x002892C0` explicitly as an original dependency and retaining the transient-stack-write distinction and scripted-caller limits in the function record.
