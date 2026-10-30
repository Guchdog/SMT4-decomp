# Independent review: `UiConfig_CopyPair` production caller surface

## Decision

The candidate matches the original 20-byte wrapper on its tested domain: two word loads from `r1` precede two word stores to `r0`; it returns the original `r0` value by returning `destination`. It also preserves the observable one-word-overlap behavior for aligned ordinary memory. However, the current accepted domain is narrower than the actual production call surface. One production path passes the odd-address read-only string `0x004656F1` through a wrapper into this 8-byte copy. The accepted candidate and its tests exclude unaligned pointers and only exercise writable synthetic RAM. Several other callers derive pointers from opaque helper outputs or dynamic buffers whose alignment and alias relation are not established by the callsite. **Do not integrate the candidate across all production callers yet.** First reproduce the odd-address case against the exact ARM body and compiled candidate, define the target-specific unaligned behavior, and resolve the shared source declaration/return type.

## Original contract and candidate evidence

Pinned original `ui_func_002adb40` at `0x002ADB40` is exactly:

```asm
ldr r2, [r1]
ldr r3, [r1, #4]
str r2, [r0]
str r3, [r0, #4]
bx lr
```

The original leaves `r0` unchanged, has no stack/calls, and reads both words before either write. The candidate in `experiments/semantic_equivalence/h2_copy_pair_candidate.cpp` performs those same two loads before its stores and returns `destination`. For valid non-null aligned pointers, this is the same observed `r0` result and copy order. With aligned 8-byte ranges, the tests cover same-pointer identity, both one-word overlap directions, adjacent disjoint ranges, and disjoint ranges.

The candidate source hash is `478eb3b4a9e77d480c4715f74bf906129cc0ca9dcb55a90c5eb82399c46ea8a6`; the candidate object hash in the function record is `2d23bae618e3679e9685afcc229dc853c0da5eb49da886740d856df851c228fd`. The two final reports are `4dcb3a6027536e21fda87ba0c1d98866bdc2e9624e7187f34dbeec5486c0a65f` (seed 7) and `237555bc88e0b2f37a3174725f59aeac2221309751327169e538a52ae18f07b4` (seed 20261024). Each reports 548/548 passing cases and detects the wrong sequential-forward-copy control. The runs compare return value, preserved GPR/SP/VFP state, RAM/stack, and read/write footprints.

Those reports explicitly constrain pointers to non-null, four-byte-aligned valid words in ordinary writable RAM. They do not cover read-only sources or unaligned source/destination pointers. The candidate's `u32*` loads/stores also make alignment a C++ precondition; behavior on an odd pointer is not established by the current C++ evidence even if a particular ARM build emits word `LDR` instructions.

## Production direct-call inventory

I scanned the pinned `.text` for ARM direct branch encodings resolving to `0x002ADB40`, then checked the owning ledger extents and decoded the callsites. This finds **28 direct `BL` sites plus one tail `B`**. A name-only source search misses many raw instruction-word callers. The following are the exact direct sites and the local argument setup visible in their original disassembly. In every row, `r0` is the destination and `r1` the source per the original body.

| Callsite(s) | Owning function | Argument setup / caller behavior |
|---|---|---|
| `0x001275A8`, `0x001275C4`, `0x001275D8` | `ui_func_0012730c` | `r0/r1` are successive `r5+8` / `r6+8` buffer addresses, then offsets advance by 8/16. Alignment and disjointness depend on the dynamic bases. |
| `0x00129574` | `ui_func_0012954c` | `r0=r4+4`; `r1` is live input at the call. The callsite does not prove its alignment or relation to the destination. |
| `0x001C8F78`, `0x001C9B18`, `0x001C9E50`, `0x001C9E9C`, `0x001C9FC8` | `func_001c8d28` | Mixes helper-returned pointers and structure fields (`[r4/r5+0x380]`, `[r6+0x14]`). Field offsets preserve alignment only if the owning object is aligned; helper-returned source/destination bases are not locally proven. |
| `0x001EAF44` | `script_vm_func_001ea928` (`TitleConfig_Calc`) | Confirm path: `r0=config` (`0x0044E0F8`), `r1=work+0x34`; copies the edited work snapshot back to global config. Both bases are four-byte aligned and disjoint. Return is ignored. |
| `0x00202AEC` | `saveLoadUI_Calc` | `r0=[r4+0x380]`, `r1` is the preceding `ui_func_0026b830` result. Dynamic buffer alignment/aliasing is not proved here. |
| `0x00238E00` | `ui_func_00238dd4` | First copies `r5+0x20` into stack scratch through `ui_func_00238e18`, then copies that stack pair to `r4`. The intermediate stack pair is disjoint; base alignment of `r4` and source depends on the caller. |
| `0x00238E28` | `ui_func_00238e18` | Wrapper calls only when incoming `r1 != 0`; it passes incoming `r0/r1` unchanged, then restores its saved original `r0` as its own return. Its callers are listed below. |
| `0x002393F8`, `0x002394BC`, `0x0023950C` | `ui_func_002392e0` | Destination includes `r4+0x55C` or `r4 + row*8 + 0x564`; sources are `r6`/`r7`. These offsets are multiples of four, but base alignment and overlap are not established by these instructions. |
| `0x0023954C` | `ui_func_0023953c` | Wrapper calls only when incoming `r1 != 0`; passes incoming `r0/r1`, then restores original `r0`. One caller supplies an odd source (see below). |
| `0x002701F0` | `script_vm_func_002701c4` | `r1=[r4+0x14]`; `r0` is the preceding helper's returned buffer. Its alignment and overlap relation are not established here. |
| `0x002EFAA0` | `SaveLoadProcess_Step` | `r1=r5`; `r0` is the preceding `ui_func_0026b830` return. Dynamic buffer contract is outside the local callsite. |
| `0x002EFC20` | `SaveLoadProcess_Write` | `r0=[r4+8]+0x80`; `r1` is a helper-returned pointer. Object alignment is plausible from the word offset but not demonstrated by this function alone. |
| `0x002F45F8` | `engine_func_002f3fc4` | Both argument registers come from the function's preceding data setup; the callsite does not state or check alignment/aliasing. |
| `0x00312FCC` | `ui_func_00312f78` | `r0=sp`; `r1=Tbb_GetPayloadData()+row*8`. Stack is aligned by the frame setup; payload-base alignment is supplied by the TBB helper and not proven by this callsite. Return is ignored. |
| `0x00358190`, `0x0035819C` | `engine_func_00357c48` | First copies wrapper-produced stack scratch to `sp+0x88`; second copies from `sp+0x88` to a destination pointer loaded from `[sp+0xD0]`. Stack side is aligned/disjoint; the loaded destination's validity/alignment is not locally established. |
| `0x00359CD8` | `engine_func_00359c9c` | Copies a pair from `sp+0x10` to `sp`; both stack ranges are aligned and disjoint. The wrapper call immediately before fills the source scratch from `r4+0x20`. |
| `0x00359F68` | `engine_func_00359f04` | Same stack-scratch pattern as `0x00359CD8`: destination `sp`, source from wrapper result in `sp+0x10`; source base `r4+0x20` depends on incoming object alignment. |
| `0x003E077C` | `engine_func_003e0738` | Wrapper first copies from `r0+0x20` to stack scratch; direct call then copies that scratch to `r4`. Stack side is aligned; the dynamic `r0`/`r4` base contracts are not proven locally. |
| `0x003E0D34` | `engine_func_003e0cf0` | `r0=r5` output cursor; `r1=r7+0x70`, with `r7=r4+row*12`. Offsets preserve four-byte alignment if the initial bases are aligned, but this function does not check the bases or whether source/output overlap. Return is ignored. |

The in-place H2 initializer adds a **tail branch** at `0x002F4E3C` (not a BL): it sets `r0=work+0x34`, `r1=config` (`0x0044E0F8`) and branches to CopyPair. The ranges are disjoint and word-aligned. It relies on the helper leaving `r0` as the destination, which the candidate's pointer return preserves. `TitleConfig_Calc` at `0x001EAF44` is the opposite direction, committing the workspace snapshot into config.

## Indirect wrapper callers and concrete out-of-domain case

The two local 40-byte wrappers make additional caller paths that a direct-call scan alone does not reveal. I scanned every aligned ARM B/BL immediate in pinned .text for targets 0x00238E18 and 0x0023953C, then verified the call instructions against their owner-function disassemblies. These wrappers forward r0/r1 to CopyPair only when r1 != 0; otherwise they take their error path. The full wrapper callsite inventory is:

- ui_func_00238e18 is called at 0x00238DF4 (ui_func_00238dd4), 0x00239680 (engine_func_0023963c), 0x00359CCC and 0x00359CE4 (engine_func_00359c9c), 0x00359F5C and 0x00359F74 (engine_func_00359f04), 0x003E0770 (engine_func_003e0738), 0x003E07F4 (engine_func_003e07a4), and 0x003E08B0 (func_003e0860). The usual destination is 8-byte stack scratch. Sources are a caller buffer plus 0x20, a dynamic helper result plus 0x20, or the engine_func_0023963c-selected buffer plus row/structure offsets. Stack destinations are aligned, while dynamic source alignment and source/destination overlap are not fully established by these callsites.
- ui_func_0023953c is called at 0x00358180 (engine_func_00357c48), 0x003E0840 (engine_func_003e07a4), and 0x003E08EC (func_003e0860). The first passes stack scratch as destination and a prior helper result plus 0x20 as source. The other two are their owners' failure paths: r0=sp+8, and r1 is loaded from literal 0x004656F1, the ERROR string address.

Both error paths pass an odd, read-only source address. In func_003e0860 at 0x003E08EC and in engine_func_003e07a4 at 0x003E0840, the wrapper sees non-null r1, calls CopyPair, reads eight bytes starting at 0x004656F1, and writes them to aligned stack scratch. This is an actual pinned production path outside the candidate's documented aligned writable-RAM test domain. It also shows that the source need only be readable; it need not be writable. The original ARM body itself performs word loads at that address, but current candidate differential reports do not establish its behavior there or the C++ alignment semantics. This must be covered before claiming safe cross-caller replacement.

Other indirect-wrapper paths have aligned stack destinations, but their source pointers (r4+0x20, a helper result plus 0x20, or a selected buffer field) come from dynamic objects or helper outputs. Their source and destination can be presumed disjoint only for the immediate stack-copy stages; the wrapper input ranges remain caller-dependent. The full-text immediate scan does not enumerate runtime-generated or indirect function-pointer calls.
## Return, alias, and interface compatibility

The original helper leaves `r0` untouched. The candidate returns `destination`, which is exactly the incoming `r0`; this preserves the observed return register. Most direct callers ignore/overwrite `r0`. `ui_func_00238e18` and `ui_func_0023953c` explicitly save and restore their incoming `r0`, so they do not depend on the helper result. The initializer tail-call is the meaningful exception: its result propagates to the initializer's caller and must remain `work+0x34`. The candidate matches it.

The load-before-store order is material for equal or one-word-overlapping aligned pointers. The isolated candidate tests exercise those cases and the wrong-forward-copy control detects a changed result. No actual caller inspected here proves an overlapping pair, but dynamic buffer callsites do not categorically rule one out. Preserve the two-load-before-store behavior in any replacement.

There is a source-interface mismatch to resolve in integration: `include/engine/leaf_matching.h` and several batch TUs declare `void ui_func_002adb40()` (no arguments), while the observed ARM ABI consumes destination/source in `r0/r1` and preserves/returns `r0`. The candidate is typed `u32* (u32*, const u32*)`. This does not change the machine calling convention, but the shared declaration and local declarations should be reconciled before making the C++ definition authoritative. `src/camp/title_flow.cpp` currently uses a local `u32`-returning function-pointer cast for its tail-call; `TitleConfig_Calc` invokes the fixed address through an untyped helper and ignores the return.

## Recommendation and follow-up

Do not replace the wrapper for the full production caller set on the current evidence. The accepted candidate is supported for aligned, valid ordinary-RAM pairs with source/destination overlap only when both ranges are valid; it is not yet supported for the actual unaligned read-only string path or opaque dynamic pointer alignments. A bounded promotion plan is:

1. Add directed original-vs-candidate cases for source `0x004656F1` to aligned stack destination and for representative read-only source mappings; compare exact resulting eight bytes under ARM11 semantics. Include unaligned destination cases only if an actual caller can produce one or if the integration promises that domain.
2. Inspect/contract the opaque helper outputs used by save/load, TBB, and parser callers; where source alignment cannot be established, either validate them or make the candidate preserve the original ARM unaligned-load behavior without undefined typed C++ accesses.
3. Preserve overlap and return behavior; update the shared function declaration to the two-register argument/return contract in an explicitly owned interface task.
4. Integrate only at the original `0x002ADB40` VMA, write the exact body extent, keep truthful ledger classification (`non_matching` on promotion), and run a caller regression covering title initializer/Calc plus the observed save/load/string/TBB windows. Do not infer UI, persistence, or whole-game behavior from the isolated helper reports.

This static review used the pinned US image hash above, `python tools/split_asm.py` at the original and listed caller functions, source callsite searches, and the existing two-seed reports. It did not compile, run tests, modify sources/ledger/headers, or use emulator/RSP/input. The direct-branch scan covers ARM-state B/BL immediate references in pinned `.text`; it does not claim to find runtime-generated or indirect function-pointer calls.
