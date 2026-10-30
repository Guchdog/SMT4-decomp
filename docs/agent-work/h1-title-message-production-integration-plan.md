# H1 title-message production integration plan

## Readiness assessment

**Planning only: the candidates are not ready for production promotion.** The editable candidate and its private ARM differential provide useful bounded semantic evidence, including four real `TitleTable.tbb` strings, but those cases call the helper directly. They do not execute the H1 caller's table lookup, establish runtime object/lifecycle behavior, or test rendered output. The shared copy routine has many unrelated callers and its candidate evidence covers only a limited non-overlapping matrix.

This document maps the smallest staged integration route. It does not approve or promote either candidate.

## Current source and build map

| Address | Ledger today | Current implementation | C++/assembly aliases and ABI observations |
| --- | --- | --- | --- |
| `0x0029F10C` | `matching`, `camp_func_0029f10c`, `src/engine/leaf_batch33_c.cpp` | A naked ARM body in `leaf_batch33_c.cpp`; it directly calls `engine_func_002c5ff4` at its two copy sites. | `ui_runtime2.cpp` declares `Camp_SetSlotMessage(const char*, u32)` but does not visibly bind that external name to `camp_func_0029f10c`. `title_flow.cpp` and `status_down.cpp` call the address under the misleading `Camp_SetFadeColor(u32 screen, u32 rgba)` alias; `unite_extras.cpp` and `asd_runtime.cpp` use integer mode aliases. These legacy reset calls pass zero in `r0`, so their register bits are compatible with null-message mode, but the declarations do not describe the actual pointer API. |
| `0x002C5FF4` | `matching`, `engine_func_002c5ff4`, `src/engine/leaf_batch37_c.cpp` | A naked ARM copy body in `leaf_batch37_c.cpp`; it returns the advanced destination in `r0` and has an aligned branch to `0x002BCF58`. | Several TUs declare `AsdMem_Copy`; at least `src/engine/asd_texture.cpp` explicitly uses `__asm__("engine_func_002c5ff4")`. Its C declaration returns `void`, although callers could observe the ARM return register through assembly. The declarations are distributed rather than represented by one visible canonical `AsdMem_Copy` declaration in `asd_symbols.h`. |

The current experiment is [h1_title_message_candidate.cpp](/C:/Users/altair/.codex/worktrees/semantic-equivalence-experiment/SMT4decomp/experiments/semantic_equivalence/h1_title_message_candidate.cpp). `CMakeLists.txt` recursively includes `src/**/*.cpp`; it does not include `experiments/`. The ledger-backed leaf batch source files are included by that glob. Therefore the experiment source is not a production replacement, and adding it beside the naked definitions would create duplicate or unreferenced implementations unless symbol ownership is changed deliberately.

The existing ARM caller paths in `ui_runtime2.cpp` initialize `ButtonHelp` before the state-2 message, then load TBB slot `0x3A`, obtain the table payload, compute `payload + 0x56*index + 0x16`, and call the message function. State 5 repeats the row pointer calculation. The corresponding static ARM instructions confirm the same arithmetic. Other known callers use null `r0` for workspace/color reset. The real-asset differential validates four strings at the derived offsets, but bypasses the caller and passes the computed pointer directly.

`include/camp/unite.h` models `ButtonHelpManager.work` at `+4` and `ButtonHelpWork` as `0x564` bytes. `ButtonHelp_Init` allocates the work object when needed and zeroes it; the title state calls it before its message call. The experimental candidate instead reads an absolute `0x0043DA28` address. Production C++ should use the typed manager/work symbol, or prove the absolute mapping in the final link, rather than carrying an experiment-only address assumption unnoticed. A matching teardown/lifetime proof is not present in the scoped source review.

## Main integration risks

1. **Symbol and declaration mismatch.** The source-visible `Camp_SetSlotMessage` name has the right input shape but no explicit alias to the ledger's `camp_func_0029f10c` in the inspected declaration. Other aliases model the first argument as a numeric mode/screen. The static library target does not by itself prove these names resolve to one definition. A final link/symbol-map check is required before interpreting a successful object build as integration.
2. **Global copy blast radius.** `0x002C5FF4` is declared as `AsdMem_Copy` across battle, UI, and engine TUs. Replacing the ledger-backed body changes behavior for all of them, not just title text. The candidate is a forward loop with a non-overlap precondition; the existing differential uses lengths through 33 and valid ordinary-memory spans. Every production caller must be checked for overlap, invalid/zero/null spans, large sizes, MMIO, and whether it observes the returned `r0` before replacing this shared symbol.
3. **Unchecked helper bounds.** The pinned helper has no per-line length guard. The candidate's safe C++ contract requires a valid initialized manager/work object, readable input through the scan, and at most 64 copied bytes per line. The four strings in the one frozen asset satisfy the limit; this does not establish it for other locales or future assets. Overlong first/second lines can overlap slots or adjacent fields in the original layout.
4. **Lifecycle and rendering.** A valid `ButtonHelpWork` pointer is a precondition. The reviewed call sequence shows initialization before the title state-2 message, but the experiments do not execute construction, teardown, live TBB binding, or rendering. A direct helper match cannot establish visible UI behavior.

## Smallest staged route after caller evidence

### Stage 0: settle the ABI and call graph

- Create one canonical declaration for the message entry with `const char*`/byte-pointer input, color in `r1`, and the actual `r0` status return. Bind it explicitly to the existing `camp_func_0029f10c` symbol. Convert reset call declarations to that same signature and use a null pointer at C++ call sites; keep raw ARM callers' zero register unchanged.
- Confirm whether `Camp_SetSlotMessage` currently resolves to the ledger symbol in the final executable/link map. Do not infer that from the declaration or the static-library build.
- Inventory all callers of both entries, including inline-assembly branches, and identify uses of copy return `r0` and copy overlap/domain assumptions.

### Stage 1: integrate the title-message behavior with the shared copier unchanged

- Replace the naked `0x0029F10C` implementation at its existing ledger-mapped source location, or provide one unambiguous implementation for the exact existing symbol and remove the old definition. Keep the H1 helper using the existing `engine_func_002c5ff4` implementation for its copy dependency in this first step. This isolates the helper change from global copy semantics.
- Adapt the candidate to use `g_ButtonHelpManager.work`/the typed `ButtonHelpWork` view. Preserve the observed null reset and non-null side effects; do not silently broaden the candidate beyond its stated safe input domain.
- Update every declaration that binds to `camp_func_0029f10c`, including the source aliases listed above, to one argument/return contract. Keep call sites that pass null compatible and preserve the actual state-2/state-5 message arguments.
- Add/maintain a production-source differential fixture that compiles the implementation actually selected by the build, rather than only `experiments/semantic_equivalence/h1_title_message_candidate.cpp`. Cover null reset, all four frozen asset rows, line/scan boundaries, workspace bytes, return value, callee-saved state, and copy arguments. Keep static caller tests separate from a live title-flow test.

### Stage 2: consider replacing the shared copy body independently

- Only after a call-site audit supports the non-overlap and ordinary-memory contract for every consumer, replace the single `engine_func_002c5ff4` definition at its mapped source. Do not add a second `AsdMem_Copy` body with a different symbol.
- Consolidate its declaration/assembly label and return type in a canonical header, while checking all existing callers that ignore the return and searching raw assembly callers for ones that consume advanced `r0`.
- Extend differential sizes to production-relevant lengths and source/destination alignments. Add caller-specific cases for any in-place or overlapping use before making a whole-engine claim. If any caller needs overlap-safe semantics, keep that caller on the original implementation or provide a separately justified wrapper; do not reinterpret this routine as `memmove`.

## Build, ledger, and acceptance checks for a future integration

- Because `src` uses `GLOB_RECURSE ... CONFIGURE_DEPENDS`, a new `.cpp` under `src/` is automatically considered after CMake reconfiguration; the current experiment file under `experiments/` is not. In-place replacement at the existing leaf-batch definitions avoids a second symbol owner but still requires confirming the final object/symbol map.
- Build the ARMv6K static library with the configured Clang flags, then perform the real final link/patch-map step. `add_library(smt4_decomp STATIC ...)` alone can leave unresolved symbols; verify there is exactly one definition per target and that `Camp_SetSlotMessage` calls resolve to the `camp_func_0029f10c` body. Check `engine_func_002c5ff4` and every alias similarly.
- Run the focused semantic differential against the production-selected object, the asset-row assertions, caller/state tests, and the relevant wider UI/engine regressions. Then verify the actual H1 main-menu scenario and rendered messages with a defined runtime procedure. Keep build success, isolated differential, caller behavior, and renderer/runtime evidence as separate statuses.
- Once production bodies intentionally differ from `code.bin`, change the two ledger rows from `matching` to `non_matching`, update their `src_file` entries if ownership moves, and update the function records with ABI/domain, caller coverage, test/report hashes, and remaining limits. Exact `asm_diff` mismatch is expected for a semantic replacement; do not preserve a false `matching` label to keep the byte baseline green.

## Recommendation, separate from approval

My recommendation is **defer production promotion**. First resolve the `Camp_SetSlotMessage` symbol binding and complete caller-level evidence. If the coordinator later authorizes a change, replace the title helper first while leaving the widely shared copy body pinned; consider the copy candidate in a separate decision after its caller audit. This sequence limits unrelated breakage and keeps acceptance evidence attributable. This is a proposed plan, not approval, promotion, or a claim of runtime equivalence.
