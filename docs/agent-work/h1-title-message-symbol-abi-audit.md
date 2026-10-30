# H1 title-message symbol and ABI audit: `0x0029F10C`

## Finding

The pinned address and the ledger-owned source definition agree on the symbol name `camp_func_0029f10c`. They do **not** agree with the source alias used by the active title UI C++ calls: `Camp_SetSlotMessage` has no explicit assembly label and no definition in `src/` or `include/`. The other C++ reset aliases also do not declare the real pointer/status contract. Current evidence does not include a production final-link map proving what `Camp_SetSlotMessage` resolves to. Do not promote the helper until the C++ call name is bound to the existing ledger symbol and the one-definition/final-link checks are performed.

## Pinned ARM contract

Pinned input: `extracted/exefs/code.bin`, configured SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The ledger row at `config/functions.csv` is `0x0029f10c,316,matching,camp,camp_func_0029f10c,src/engine/leaf_batch33_c.cpp`.

The source body at `src/engine/leaf_batch33_c.cpp:8730` is the naked ARM implementation under that exact C-linkage name. The prologue and body establish the register ABI directly:

- `r0`: optional NUL/LF-delimited message byte pointer; zero selects reset/clear mode.
- `r1`: color word, stored at work `+0x4CC` on both paths.
- Return `r0`: `0xFF` for the null/reset path and `1` for non-null input. The entry sets `r0=0xFF` before its null branch; the non-null epilogue sets `r0=1`.
- Preserves `r4-r8` and `lr` with `push`/`pop`; SP is restored. `r2` loads the global manager literal and `r7` receives manager `+4` work pointer. Neither manager nor work pointer is null-checked.

The function record gives the pinned extent `[0x0029F10C,0x0029F248)` and records the terminal `POP {...,pc}` at `0x0029F240` followed by the `0x0043DA28` literal at `0x0029F244`. This is a helper ABI, not a two-integer mode/screen API. A correct common declaration needs a pointer first argument and a `u32` return if it is to describe the observed status register.

## Source declarations and callsites

| Source location | Declared name and type | Active call shape / binding evidence |
| --- | --- | --- |
| `src/ui/ui_runtime2.cpp:56` | `extern "C" void Camp_SetSlotMessage(const char*, u32)` | Active calls at `:3978` and `:4180` pass the selected help-row pointer and `0x323232FF`. This declaration does **not** name or bind `camp_func_0029f10c`; no definition of `Camp_SetSlotMessage` was found in source/header search. The similar call at `:1268` is inside a `#if 0` reconstruction draft and is not compiled. |
| `src/camp/title_flow.cpp:55` | `extern "C" void Camp_SetFadeColor(u32 screen, u32 rgba)` | Only corresponding observed call is inside inline ARM in `TitleConfig` setup: raw `.word 0xebfea8c2` at `:291` is a `BL` to the address, preceded by `r0=0`, `r1=0x323232FF`. The inline branch does not relocate against the C++ alias. It is reset mode, despite the misleading `screen` parameter name. |
| `src/ui/status_down.cpp:116` | `extern "C" void Camp_SetFadeColor(u32 screen, u32 rgba)` | Inline raw `.word 0xea003028` at `:1212` is an unconditional tail `B` to the helper after restoring the caller's saved registers; it sets `r0=0` and loads color into `r1`. This is reset mode. A tail branch forwards the helper's `r0` to the original caller. |
| `src/camp/unite_extras.cpp:137` | `extern "C" void camp_func_0029f10c(u32 mode, u32 color)` | Active C++ calls at `:372` and `:436` pass `(0, 0x323232FF)`, so the first register is null/reset, not a mode. C linkage makes the declared name spelling match the ledger symbol, but type and return are inaccurate. |
| `src/engine/asd_runtime.cpp:130` | `extern "C" void camp_func_0029f10c(u32 index, u32 color)` | Active call at `:2037` passes `(0, 0x323232FF)` for reset. Same actual C-linkage spelling, inaccurate `index` name/type and missing return. |
| `src/engine/leaf_batch29_c.cpp:40` | `extern "C" void camp_func_0029f10c()` | Raw ARM body at `:3787` emits `bl camp_func_0029f10c`; its setup is register based and requires only the symbol spelling. The audited nearby path is a null/reset call. The zero-argument `void` declaration hides the actual register contract. |
| `src/engine/leaf_batch33_c.cpp:8730` | `extern "C" __attribute__((naked)) void camp_func_0029f10c()` definition | Exact symbol spelling and ledger source ownership, but C++ signature still omits inputs and return because the body is hand-written assembly. |

Other `Camp_SetFadeColor` declarations found in `src/ui/status_down.cpp` and `src/camp/title_flow.cpp` have no C++ call expressions. Their raw literal branches are direct-address calls, not evidence of symbol binding. No declaration of `Camp_SetSlotMessage` with `asm("camp_func_0029f10c")` (or equivalent alias) exists in the packet's source/header tree.

### Pinned direct-call inventory

I scanned every aligned ARM word in the pinned configured text span `[0x00100000,0x003FE624)` for immediate `B`/`BL` encodings whose computed destination is exactly `0x0029F10C`. The scan found 106 branch encodings: 94 `BL` and 12 tail `B`. The raw-address sites, grouped by branch type, are:

- `BL`: `00180998 00180D6C 00181B94 001839B0 00183C10 001892E0 0018AA74 0018BA2C 0018BC60 0018BCE8 0018DCA8 0018E0D4 0018E50C 00190B20 0019C308 001A2088 001A2354 001A23D8 001A2518 001AFE64 001B04E8 001B0530 001B0574 001B05BC 001B0600 001B1140 001C71FC 001C82BC 001C9518 001CC140 001CC4B8 001CC600 001CC718 001CC778 001CC824 001CC8E0 001CFC14 001D0C78 001E9ADC 001EA15C 001EAA38 001EADFC 001EAEF0 00202E70 00204494 002046D8 002047BC 00204D38 00214A08 00222F30 0022FC74 002932C8 00296B08 00297F00 0029FFE4 0028D8E4 002A0264 002CFEE0 002DACC0 002F4DFC 0032CE10 0032D1C4 0032DF6C 00331688 00332D2C 00333548 003336E4 0038253C 003830B8 003831B0 003A1168 003A3630 003A3654 003A3810 003A3834 003A3CF0 003A3ED8 003A5F64 003A5FF8 003A7330 003A7CC0 003A7FA8 003A8404 003A8908 003A89C8 003A8BD0 003A91B0 003A9D04 003A9DB8 003AB900 003AC2A0 003AC330 003B9244 003BBBAC`.
- Tail `B`: `001B064C 00204CFC 0022FD4C 00233E10 00233EDC 00242198 0026CC18 00290838 00293064 00297EE0 00299C84 003A0F04`.

This is an encoding sweep of the pinned text, not a CFG/reachability proof. At the two H1 help-string sites `0x001E9ADC` and `0x001EA15C`, the preceding instructions derive `payload + 0x16 + 0x56*index`, load `r1=0x323232FF`, then call the helper. The separate title-config site `0x002F4DFC` loads the same color and sets `r0=0`. The visible source inventory also includes numerous other null/reset invocations and non-null text buffers (including formatted stack buffers in other subsystems). The 12 `B` sites tail-transfer into the helper and therefore propagate its status register to their caller; the surrounding caller's ultimate observation was not resolved here. Most `BL` sites overwrite or do not visibly use `r0` immediately afterward, but a whole-program return-value def-use audit is not established by this bounded review.

The reconstructed source only names a subset of pinned direct sites. Inline `.word` branches and literal-address calls deliberately have no source-level symbol relocation, so searching source identifiers alone is not a complete caller inventory. No indirect function-pointer invocation was identified by this review, but no whole-image dataflow proof excludes one.

## Build and linker/map evidence

`CMakeLists.txt` uses `file(GLOB_RECURSE SMT4_SOURCES CONFIGURE_DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/src/*.cpp")` and builds `smt4_decomp` as a **static library**. `src/engine/leaf_batch33_c.cpp` is in the source tree and owns the ledger implementation. The experiment candidate is outside that glob. A static archive can retain undefined symbols and is not final-link proof.

Existing build outputs searched during this audit did not provide a production final executable/map or a symbol table resolving `Camp_SetSlotMessage` to `camp_func_0029f10c`. Existing private candidate ELFs/reports are experiment outputs, not the production `smt4_decomp` final image, and their test harness/link stubs cannot establish production symbol resolution. The pinned image proves branch destinations are raw address `0x0029F10C`; it cannot prove how the current C++ declaration links.

## Minimal safe canonical declaration and binding

Before source promotion, use one canonical declaration for the existing exported C symbol, e.g. `extern "C" u32 camp_func_0029f10c(const char* text, u32 rgba);`, in a shared header included by every C++ caller. Change the existing definition prototype to match this declaration even while its naked assembly body is retained; do not permit incompatible per-TU prototypes. If product-facing readability needs the alias `Camp_SetSlotMessage`, make it an explicit wrapper or a compiler asm-label alias to the exact canonical symbol, and use that one declaration everywhere. Do not declare both aliases as independent external C symbols.

Convert reset C++ call expressions to `(nullptr, rgba)` and keep raw ARM paths unchanged (`r0=0`, `r1=color`). Leave text paths typed as `const char*`. Retain a `u32` return in the common contract so null returns `0xFF`, non-null returns `1`, and tail-call propagation is expressible. Preserve one production definition at the ledger-owned location. Before claiming the ABI seam is closed, inspect the final production link/map or symbol table and require exactly one `camp_func_0029f10c` definition, no unresolved `Camp_SetSlotMessage`, and no duplicate veneer/wrapper with different status behavior. The project currently has no such final-link evidence in the reviewed artifacts.

## Limits and next proof

This is read-only static recon against the pinned image and frozen source packet. I did not build, test, emulate, patch source, or modify the board. Branch-encoding inventory is not reachability analysis; the broader 106-site callers are not all tied to readable caller functions here; callers that might consume returned status beyond tail propagation need def-use tracing; and no production link map or runtime behavior is proven. A separate reviewer/integrator should verify the canonical prototype/binding proposal, map all non-H1 caller effects, then perform a controlled production link/map and caller-level validation before any promotion decision.
