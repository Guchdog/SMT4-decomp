# H2 TitleConfig initializer production integration plan

## Recommendation

Keep the production initializer wrapper at 0x002F4CA0 unchanged for the current Calc-only integration. Do not treat the reviewed orchestration candidate or the State-9/10 caller composition as an initializer promotion. The candidate is semantically promising under declared HLEs, but there is no reviewed production-source patch for it, and the current Calc cave cannot hold both compiled bodies.

For a later combined Calc+initializer patch, use a coordinator-owned multi-cave patch builder. Keep Calc at its currently verified cave address 0x003FE624 and place the initializer candidate in a second independently verified executable text cave of at least 552 bytes (plus alignment). Patch only each original entry instruction with a branch and retain the original function bodies and literal pools otherwise. No second suitable H2 cave is established by the current evidence. If none can be proven in the pinned image, the combined initializer patch is blocked pending a placement solution; do not squeeze blobs into unverified zero bytes or overwrite the original literal pool.

## Production source proposal and ABI

The current production definition is a naked ARM wrapper in src/camp/title_flow.cpp, `titleConfig_func_002f4ca0(void*)`, spanning [0x002F4CA0, 0x002F4EDC) (572 bytes). Preserve this symbol, source file, original extent, and entry address. The readable candidate is `candidate_002f4ca0(void*)`: it ignores r0, follows the original direct call order, and returns the result of `UiConfig_CopyPair` in r0. The original assembly tail-branches to that helper, which leaves `work+0x34` in r0. Before replacing the naked body, audit every caller and callback type, then declare the C++ function with an ABI-compatible return type that preserves this observable r0 result; the candidate's u32 return is the current evidence-backed model. Do not silently retain a `void` definition whose compiled epilogue may change r0. Keep the ignored pointer argument.

Use the existing `TitleConfigWork` layout/assertions in include/camp/title_flow.h and the existing global declarations. Preserve exact operation order: allocation and global publication; Calc then Draw task creation and Calc handle store; sprite group initialization/bind; sprite and cursor setup; state/halfword initialization before `UiConfig_FillPair`; both async table requests; sound and reset-mode calls; three config byte mapper calls and stores; final eight-byte pair copy. Keep allocator, task factories, sprite/cursor setup, async loading, sound, UI reset, three mappers, fill/copy helpers as original dependencies until their concrete contracts are promoted. Preserve the allocation's unchecked/null behavior and do not claim task scheduling or asynchronous readiness from the initializer itself.

The existing candidate evidence is based on a separate experiment TU and must not be reused as proof of a production TU build. Candidate source SHA-256 is `9b2b181a2f79683cf456b07b26484fa7d5390672b8662b71b469553280c665c5`; its ARM body is 552 bytes with no ELF relocations; object SHA-256 is `d4d7282f1cc26d99f361cb9d31619ed9250bb41522cba22d161deaf4c1b7ceba`. Those facts come from the corrected run `build/agent-work/H2-semantic/h2-init-orchestration-candidate/run-001/experiment-final-v2/report.json` (SHA-256 `f47bd5d1b460470ae9881614e3f6c756c5a1b3cccd60d16913b8f36b66c0e19c`) and are candidate-build facts only.

## Combined patch placement

The pinned US v0.1.0 image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Its `.text` begins at VMA 0x00100000, file offset 0, size 0x002FE624, and aligned size 0x002FF000. The only H2 cave reviewed so far is the zero-filled page tail 0x003FE624..0x003FEFFF, capacity 0x9DC (2,524 bytes).

| Body | Reviewed candidate bytes | Placement consequence |
|---|---:|---|
| TitleConfig_Calc | 2,096 | Fits at 0x003FE624; leaves 428 bytes. Its final production patch rebases four audited local R_ARM_ABS32 references. |
| Initializer orchestration | 552 | Fits alone in the cave, but no standalone initializer production patch exists. The candidate has no ELF relocations. |
| Calc + initializer | 2,648 | Exceeds the single cave by 124 bytes, before any optional alignment gap. |

An entry branch is written at the original function address and does not consume cave capacity. However, the combined patch needs a second safe body location: with Calc occupying 0x003FE624..0x003FEE64, the remaining tail is only 428 bytes. The H1 runtime cave at 0x003FE720 lies inside the Calc range in this placement and is not an available second cave. The current metadata exposes only one aligned text-padding page; no other executable zero range has been audited for code/data references or loader behavior.

The current initializer candidate embeds absolute addresses for task/resource strings held in the original initializer's inline pool: 0x002F4E84, 0x002F4E9C, 0x002F4EB4, and 0x002F4EC4. Its 552-byte body spans offsets 0..551 from 0x002F4CA0, through address 0x002F4EC8. Copying that body directly over the original function would overwrite those referenced strings. A branch from 0x002F4CA0 to a second cave leaves the original pool intact and keeps these absolute pointers valid. If an in-place strategy is considered instead, it requires an explicit literal-pool relocation/retargeting design plus tests; the current candidate bytes cannot be copied in place as-is.

The current `tools/h2_calc_code_patch.py` is Calc-only: it pins the image/layout/cave, expects the Calc candidate and its four local absolute relocations, then emits one entry branch plus one cave record and verifies IPS application. It is not a multi-candidate production linker. `tools/semantic_experiment.py::patch_image` supports only its relocation-free leaf allowlist and likewise does not accept these H2 non-leaf/initializer symbols as a production path. A new integrator-owned builder should accept the extracted production symbols, pin image/source/object hashes and all guest/file ranges, allocate disjoint aligned caves, emit both original-entry branches, strictly validate the Calc relocation table and the initializer's empty relocation set, reject unknown relocations and cave overlap/overflow, and independently apply the serialized IPS to prove it recreates the measured patched image. Keep extracted `code.bin` immutable.

## Caller composition and current evidence boundary

The candidate differential executes the original initializer and candidate from identical initialized snapshots with deterministic HLE boundaries. The corrected run passes five cases per seed and detects the wrong group count; it checks call arguments/order, work/global/config bytes, return/PC/SP and preserved registers. This is useful initializer-body evidence, not production source, scheduler, or runtime proof.

The offline State-9/10 caller runner compares the pinned title caller and readiness/reset path with original helper HLEs. Its current final report (`build/agent-work/H2-semantic/h2-calc-production-integration/run-001/checks/final-caller-20261026/report.json`, SHA-256 `144119150c1c6fbfbb57add4a67a017265088599e58d68b7d67143937718e8b8`) reports 3/3 cases and detects the wrong registered Calc callback control. It loads the Calc-only production-patched image, then compiles/injects the initializer candidate at a synthetic address and branches 0x002F4CA0 there for the patched machine. It therefore validates this caller composition under HLEs, but it does not validate the initializer at a final production cave VMA or a merged IPS. It verifies registration/readiness/reset behavior; it does not schedule or execute the registered Calc callback. Task factory, allocator, async resources, cursor/sprite setup, sound/reset services, and task activity are HLE boundaries.

Required next caller evidence after a multi-cave patch is available:

1. Build one merged image/IPS from production-extracted Calc and initializer symbols, with distinct final cave VMAs. Run the existing State-9/10 caller cases against that exact patched image without synthetic init re-injection; preserve the callback registration mutant and State-9 gate control.
2. Add a caller-composed scenario that reaches the initializer, observes `g_TitleConfigWork` and Calc task registration, then executes the registered production Calc at its final cave address using initialized work and recorded task state. Compare the original and patched traces/memory/ABI at synchronized boundaries. Keep task scheduler/service HLEs explicit.
3. Run the focused source/TU and patch tests, then one coordinator-owned wider build/regression after all workers stop. Verify both production symbols, branch destinations, relocation records, IPS application, patched-image hash, and bytes outside authorized patch records. Run `asm_diff.py` for each changed source symbol as an expected byte diagnostic; do not weaken it or label differing bytes `matching`.
4. Keep real Azahar input/edit/cancel/confirm/re-entry/persistence checks as separate future evidence. Existing runtime work does not prove those H2 behaviors, and this plan does not request or perform runtime, RSP, or host input.

## Build, ledger, and promotion

Once placement is solved, replace only the initializer wrapper body in `src/camp/title_flow.cpp`, preserving its symbol and TU. Compile that affected TU into a fresh private output and extract `titleConfig_func_002f4ca0`; fail closed unless its body size, relocation set, branch assumptions, and final caller composition are supported by the actual object. The experiment candidate's size/relocations do not guarantee the production emission. The Calc production TU is `src/engine/leaf_batch46_b.cpp`; the accepted Calc integration already records its production symbol and final-address evidence. Rebuild every affected TU/header consumer, run both initializer and Calc focused differential suites plus the exact merged caller composition, and let the coordinator perform the one wider batch closure.

Keep `config/functions.csv` row `0x002f4ca0,572,matching,camp,titleConfig_func_002f4ca0,src/camp/title_flow.cpp` unchanged until a reviewed production patch exists. On promotion, change only its byte classification to the supported `non_matching` label while preserving original address/extent/symbol/source; add the actual production source/object/IPS/patched-image hashes and bounded evidence to `docs/function-records/0x002f4ca0.md`. Keep the Calc ledger/function record independently truthful. A candidate experiment or caller pass is not a production replacement. Acceptance must report that allocator/task/resource/input helper bodies remain original or mocked and that full H2 runtime/persistence remains open.

## Read-only evidence inspected

- Initializer function record and reviewed orchestration/dependency reports; candidate source and corrected experiment report above.
- Existing Calc source-integration plan and production report `docs/agent-work/h2-calc-production-integration.md`; accepted Calc patch artifact hash `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d`.
- `docs/agent-work/h2-integration-path-contract.md` and its independent review, which identify the one verified text cave and limitations of both current patch tools.
- `tools/h2_offline_caller_composition.py` and its final-caller report above; this runner uses an injected init body and does not execute the registered Calc.
- `src/camp/title_flow.cpp`, `include/camp/title_flow.h`, `config/functions.csv`, `config/game_info.json`, and the H2 milestone record.

No compilation, runtime, Azahar, RSP, profile, keyboard, or mouse operation was performed for this plan.
