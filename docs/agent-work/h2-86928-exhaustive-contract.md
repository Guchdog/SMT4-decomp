# `0x00286928` exhaustive static contract and conversion assessment

## Structured handoff

- **Task / owner:** `h2-helper-00286928-exhaustive-contract` / `h2_86928_contract`
- **Owned report:** `docs/agent-work/h2-86928-exhaustive-contract.md`
- **Reference:** `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; function address `0x00286928`, span 820 bytes; function-body bytes SHA-256 `13599a73fefa7f8ed72d8251e769b2302486c973169be524785830699b7f7c6c`.
- **Source identity:** `src/engine/leaf_batch45_a.cpp`, SHA-256 `7839733a03da5cd79e4553c33cc4206f85fb942613354e25f92c7d0108eddcda`; it embeds the pinned ARM body.
- **Evidence level:** static ARM disassembly and static direct-call-site scan only. No implementation, build, differential run, runtime capture, or emulator action was performed.
- **Recommendation:** a complete C++ contract is recoverable, with unresolved direct dependencies retained at their original addresses. A 820-byte fit is plausible but **not established**; do not replace this whole function with the existing small `r3=6` fast-path slice. Require a complete implementation and a private size/interworking check before integration.
- **Next action:** implementation owner should model the full selector/state machine below, retain the enumerated callees as original ARM dependencies where their contracts are not independently integrated, then compile to a task-private directory and report code size, relocations, ARM/Thumb call state, and all offline differential results.

## Identity, ABI, and evidence boundary

The body is ARM code at `0x00286928..0x00286C4F` (202 32-bit instructions); the final 12 bytes at `0x00286C50..0x00286C5B` are literal-pool data. The total span is 820 bytes. The original prologue saves `r0-r8`, `r10-r12`, and `lr` (13 words), saves `d8`, and allocates 12 bytes. The epilogue restores the local frame, `d8`, `r4-r11` and returns through the saved LR. Thus normal returns restore SP and callee-saved integer registers `r4-r11` and VFP `d8` (the lower half of `s16`). The routine uses ARM state and VFP instructions; execution requires the relevant VFP/ABI state.

The raw AAPCS entry is six 32-bit words: `r0`, `r1`, `r2`, `r3`, `[entry_sp]` (arg5), `[entry_sp+4]` (arg6). It loads arg5 into `r4`; arg6 is transferred through `s16` using `vldr` and later passed onward with `vstr`. Do not assign arg6 a float meaning: the observed operation is a raw word transfer through a VFP register. After the 13-register push, `vpush {d8}`, and 12-byte local allocation, the original stack arguments are at current `sp+0x48` and `sp+0x4c`. At helper calls, current stack alignment is 8-byte aligned if entry SP was aligned.

`r0` and `r1` are saved and forwarded to `0x0028E974` on paths that call it. Incoming `r2` is copied to `ip` and used only as a zero/nonzero branch predicate in this body; it is not directly dereferenced. Incoming `r3` selects a global work pointer and local mode/flags. Arg5 (`entry [sp]`) is copied into object `+0x36` on the incoming-r2-zero path and gates two later calls. Arg6 is forwarded to `0x0028E974` through the stack. The routine clobbers caller-saved registers/flags as usual; a candidate test must compare callee-saved state, SP, return and relevant VFP state, not require caller-saved scratch identity absent a caller contract.

The dynamic run-002 evidence is bounded: it observed the nested target `0x00221168`, callback raw return `r0=0`, and outer handler return `r0=2`. Static `0x00221168` calls this helper with `r3=6`, arg5 `1`, arg6 `0`, and leaves the helper return in callback `r0`. The trace did not capture the helper's six entry arguments, selected object bytes/pointers, internal PC, or causal branch. The static contract does not prove which internal route produced the observed zero or assign high-level meaning to its fields or return values.

## Selector setup and common writes

The body loads the selector table base from literal `0x0043E188`. The following map is for the raw unsigned selector `r3`; values not named in a comparison follow the default path, not an out-of-range rejection.

| Raw `r3` | Selected pointer `r5` | Local selector after setup | Byte written to `P+0x5E` | Conditional `P+0x5F` flag |
|---|---|---:|---:|---|
| `11` | `*(u32*)(0x0043E188+8)` | 11 | 1 | 1 |
| `12` | `*(u32*)(0x0043E188+0xC)` | 12 | 0 | 0 |
| `13` | `*(u32*)(0x0043E188+8)` | 11 | 1 | 1 |
| `14` | `*(u32*)(0x0043E188+8)` | 11 | 0 | 0 |
| `15` | `*(u32*)(0x0043E188+8)` | 11 | 0 | 0 |
| `19` | `*(u32*)(0x0043E188+8)` | 19 | 0 | 0; special pointer and later branch |
| all other 32-bit values | `*(u32*)(0x0043E188+4)` | original value | 0 | 0; includes 6 used by callback `0x00221168` |

The `+0x5E` byte is selector-derived local mode; the `+0x5F` byte is a separate flag. The routine first stores a selector-derived byte at selected pointer `r5+0x2D` and stores local mode at `r5+0x5E`. `+0x2D` is 1 only for raw selectors 13 and 15, and zero otherwise. There is no null check before these stores. On the incoming-`r2==0` path, a nonzero `+0x5F` flag writes byte 1 at `r5+0x5F` and at the default pointer previously loaded from global `+4`; this happens for raw selectors 11 and 13, and the pointers may alias so both stores remain observable. This path can also write `r5+0x36`, `r5+0x10`, and conditionally `r5+0x2E`.

The `r5+0x10` word is selected by a compare against normalized selector 6: equal loads literal `0x035AB9FF`, otherwise literal `0x320202FF`. The store is unconditional on this path, including when `r5` is null (which faults). Selector 13/14/15 normalization means none of those use the selector-6 literal.

## Complete branch/call map

Let `P` be selected `r5`, `S` the normalized local selector, `M` the byte stored at `P+0x5E`, `F` the separate conditional `P+0x5F` flag, `I2` incoming `r2`, and `A5/A6` the two stack arguments. Callee effects below are additional to the local effects. All helper addresses are fixed original dependencies unless separately reconstructed and validated.

### Incoming `I2 != 0`

After common writes, the code checks `P` and byte `P+8`. A null `P` faults at the unconditional common store to `P+0x2D` (`0x0028699C`), before the incoming-r2 branch or any `P+8`/`P+0x2E` read; it is not a supported null-safe case. For nonnull `P` with `P+8==0`, the following `P+0x2E` branches apply.

1. If `P+8 == 4`, return raw `1` (`0x286C38`) after the two common byte writes. No direct callee or further local write occurs.
2. If `P+8 == 5`, load word `P+0x18`, call `0x0028DF54` with that word in `r0`, then return raw `1` (`0x286C40`). In the pinned callee, `0x0028DF54` loads `p = *(u32*)(0x0044DE98+0x20)`, stores byte zero at `p+0x3B`, stores the input word at `p+0xA8`, and returns. The indirect pointer is not null-checked. Object/global aliasing can affect final state and ordering.
3. If `P+8 == 0`, read byte `P+0x2E`:
   - If zero and `S` is neither 11 nor 19, return raw `1` without another call.
   - If zero and `S` is 11 or 19, check the default pointer retained in `r0` (loaded from `0x0043E188+4` during selector setup). If it is non-null and byte `[r0+8]` is nonzero, return raw `0` without these calls. If the pointer is null or that byte is zero, load the word at `P+0x18` and pass that word to `0x0028DF54`, then call `0x0028DF3C(0xFFFFFFFF)`, then `0x0028DF0C(0)`, then return raw `1`.
   - If nonzero, clear byte `P+0x2E`; call `0x0028E974(P, raw_r0, raw_r1, S, stack args 0x1A, 1, 0)`; then if byte `P+0x35` is zero call `0x0028DF98(P, byte[P+9])`; return raw `0`. In this branch arg6 is not forwarded; the third stack word is zero.
4. For `P+8` other than 0, 4, or 5, call `0x002C1F28()`; zero returns raw 0. If nonzero, call `0x002B89A0()`; zero returns raw 0. If nonzero, reread `P+8`; state 3 or state 0 returns raw 0. Otherwise call `0x002B8D24(P, byte[P+9])`, then store byte 3 at `P+8` and byte zero at `P+0x35`; return raw 0. Callee memory effects precede these two stores.

### Incoming `I2 == 0`

The code writes byte `M` to `P+0x5E`. If `F != 0`, it stores byte 1 to `P+0x5F` in both `P` and the default global pointer loaded from `0x0043E188+4`. It writes low byte of `A5` to `P+0x36` and the selector-dependent word literal to `P+0x10`. These accesses are unchecked. A null selected pointer faults at the first +0x2D store before any selector-specific state path.

1. If byte `P+8` is nonzero, set byte 1 at `P+0x2E`, call `0x002B8D24(P, byte[P+9])`, set byte 3 at `P+8`, set byte zero at `P+0x35`, and return raw 0. This route does not call `0x002C1F28`/`0x002B89A0` and skips the common update loop below.
2. If byte `P+8` is zero, call `0x002C1F28()`; if nonzero, call `0x002B89A0()`. A nonzero result from both calls returns raw `1` immediately. Otherwise call `0x0028E974(P, raw_r0, raw_r1, S, stack args 0x1A, 1, raw_A6)`.
3. After that `0x0028E974` call, if `S` is 11 or 19, call `0x002B787C(word[P+4])` and store its result word at `P+0x20`.
4. If byte `P+0x35` is zero, call `0x0028DF98(P, byte[P+9])`.
5. If `A5 != 0`, call `0x002C4BF0(word[P+4], 0x20)`, then `0x002B90F0(word[P+4], 0x40)`.
6. Set byte zero at `P+0xA12`. For `i=0..5` ascending, call `0x002F5B2C(i)` and store its low byte at `P+0xA13+i`; then call `0x002D65B4(i)` and store its low halfword at `P+0xA1A+2*i`. Each iteration's first call/store precedes its second call/store.
7. If byte `P+9` is 7, 8, or 9, call `0x0028DF70(0)`. If return equals 5, store byte 1 to `P+0xA26`, call `0x002B8CCC()` and store its low byte at `P+0xA12`, then call `0x002B8B78(0xDC)`.
8. If `S==19`, call `0x002B8584` after setting `r0=1`; other argument registers retain their path values. This occurs after the optional state-7/8/9 sequence. Return raw 0.

The alternate zero-`P+8`/`P+0x2E!=0` incoming-`I2!=0` path clears `P+0x2E`, calls `0x0028E974` with stack third word zero, optionally calls `0x0028DF98` if `P+0x35` is zero, then returns 0. It does not execute the six-element update loop.

### Global query dependencies whose local contracts are narrow

- `0x002C1F28()` reads signed word `0x0043E0BC`; if negative it returns the sign-extended byte at `0x0043E0B8`, otherwise returns zero. This describes the queried values, not the broader global lifecycle.
- `0x002B89A0()` reads pointer `*(u32*)0x0044DC20`; returns 1 if null or if word at pointer `+0x352C` equals `0x14`, else 0. Pointer validity outside the null case must be controlled.
- `0x002B8D24(P, byte[P+9])` has its own 19-entry dispatch and multiple dependencies. Keep it original or separately validate it; this contract does not collapse its effects.
- `0x0028E974`, `0x002B787C`, `0x0028DF98`, `0x002C4BF0`, `0x002B90F0`, `0x002F5B2C`, `0x002D65B4`, `0x0028DF70`, `0x002B8CCC`, `0x002B8B78`, conditional `0x002B8584`, and the `0x0028DF54/3C/0C` callees remain direct original dependencies unless independently reviewed. Do not assume these are pure or that their effects are only the visible call-site values.

## Global/object reads and writes

Explicit global reads are the pointer table at `0x0043E188` (`+4`, `+8`, or `+0xC` according to selector), selector-query globals `0x0043E0BC`/`0x0043E0B8` through `0x002C1F28`, service pointer `0x0044DC20` through `0x002B89A0`, and callback/service pointer `0x0044DE98+0x20` through `0x0028DF54`. The latter globals may alias the selected object or other fixture memory; a supported test must map them and either model aliases or explicitly restrict them to disjoint ordinary RAM.

Explicit reads from selected object `P`: bytes `+8`, `+9`, `+0x2E`, `+0x35`; words `+4`, `+0x18`; and selector/callee-dependent data passed through `+4`, `+9`, and `+0x18`. Explicit local writes: byte `+0x2D` is 1 for raw selectors 13 and 15 and zero otherwise; byte `+0x5E=M`; conditional byte `+0x5F=1`; low byte `A5` to `+0x36`; selector literal word at `+0x10`; conditional byte `+0x2E` set/cleared; state byte `+8=3` and `+0x35=0` on two branch families; conditional word `+0x20`; byte `+0xA12`; six bytes `+0xA13..+0xA18`; six halfwords `+0xA1A,+0xA1C,+0xA1E,+0xA20,+0xA22,+0xA24`; and conditional byte `+0xA26`. Every list is path-local; direct callees can perform additional effects and can fault before later local writes.

## Direct caller inventory and limits

A static aligned ARM BL-immediate scan of the pinned image found these 22 candidate direct call sites, mapped to their ledger function ranges. This is a code-image scan, not proof of all indirect/Thumb dispatch or of runtime reachability. The six argument values are fully decoded here only for callback `0x00221168`.

| Call site | Containing ledger function |
|---|---|
| `0x001AA190` | `engine_func_001AA144` |
| `0x001C2970` | `engine_func_001C291C` |
| `0x001DC7FC` | `engine_func_001DC7B4` |
| `0x001DC860` | `engine_func_001DC808` |
| `0x001ECACC` | `engine_func_001ECA84` |
| `0x001ECB28` | `engine_func_001ECAD8` |
| `0x001ECB94` | `engine_func_001ECB34` |
| `0x001ECC00` | `engine_func_001ECBA4` |
| `0x002117DC` | `ui_func_0021178C` |
| `0x00211890` | `ui_func_00211824` |
| `0x00211924` | `engine_func_002118A0` |
| `0x00221104` | `engine_func_002210B0` |
| `0x0022115C` | `engine_func_00221114` |
| `0x002211EC` | `engine_func_00221168` |
| `0x0024BB70` | `ui_func_0024BAF4` |
| `0x00255080` | `script_vm_func_0025506C` |
| `0x00259484` | `func_00259454` |
| `0x002CD7B8` | `ui_func_002CD754` |
| `0x002D7B3C` | `engine_func_002D7AE4` |
| `0x002ED4D0` | `engine_func_002ED47C` |
| `0x0030A06C` | `engine_func_00309FDC` |
| `0x0031E948` | `engine_func_0031E8E8` |

At `0x002211EC`, callback `0x00221168` passes arg1 from `0x0028686C`, arg2 from `0x00296F60`, arg3 from a second `0x00289640` call, selector 6, arg5 1 and arg6 0. The helper's raw return passes through as callback `r0`. Other callers need individual argument and continuation review before their caller domains can be claimed.

## Can a complete C++ body fit in 820 bytes?

The existing 820 bytes contain 202 ARM instructions plus a 12-byte literal pool. The branch logic above can be expressed as a complete C++ state machine while leaving direct dependencies at their original addresses; their unresolved high-level semantics do not require fallback to the original `0x00286928` body. However, no candidate C++ body or compiler measurement is available in this recon, so there is no evidence that a complete implementation fits the original 820-byte placement. An `-Oz`/`minsize` implementation may fit after compiler optimization, but the many direct calls, stack-argument setup, VFP raw-word handling, and six-iteration loop make that a measurement question, not a static conclusion.

Do not use the existing r3=6 / `r2!=0` partial slice as replacement for the function: it omits valid raw selector values, `r2==0`, and multiple states/callees. If the complete candidate exceeds the 820-byte slot, the valid options are a separately measured/reviewed code-cave or trampoline layout preserving the full contract, or keeping the original body; a dispatcher may not silently send unimplemented cases to a semantically unsupported fallback. A target-slot fit requires checking all branch/literal reach, relocations, entry pointer bit/state, BL/BLX target state and return interworking after compilation.

## Full offline differential and caller-composition plan

1. **Freeze and identify inputs.** Pin image, full source, candidate source/object, compiler/version/flags, and original helper bytes. Compile candidate to a task-private directory; report exact body bytes/relocations. No canonical build cache or shared runner edits.
2. **Set up original-vs-candidate ARM execution.** Execute the original image and the candidate at the same entry address with identical 8-byte-aligned stack and mapped registers/memory. Enable VFP/FPEXC because original saves/restores `d8` and uses `s16`. Capture raw return, SP, `r4-r11`, `d8`, fault PC/class, every ordered global/object write, and ordered direct-callee entries with arguments. Compare the supported memory region and all known indirect service targets.
3. **Enumerate selector boundaries.** Test raw `r3` values `0..20`, all selectors that compare specially (`11,12,13,14,15,19`), high-bit values `0x80000000` and `0xFFFFFFFF`, and values adjacent to every special selector. Test both incoming `r2==0` and representative nonzero values (1, `0xFFFFFFFF`) for each. Assert the selector-derived pointer/normalized selector/flag and literal choice.
4. **Enumerate state and branch boundaries.** Cross each `r2` side with states `P+8` values `0,1,2,3,4,5,6,255`; vary `P+0x2E` zero/nonzero for the state-zero route; `P+0x35` zero/nonzero; `P+9` values `6,7,8,9,10,255`; arg5 `0,1,0x100,0xFFFFFFFF`; raw arg0/arg1 variation; arg6 bit patterns `0`, `0x3F800000`, `0xFFFFFFFF`, and deterministic varied words. Exercise both outcomes of global query callees and the `0x0028DF70` return-5 branch. Use multiple deterministic seeds and directed sentinels.
5. **Dependency coverage.** First run real original callees and valid controlled backing globals. For direct calls, assert exact order, raw args, stack words and all caller-visible writes, including `0x0028DF54` pointer effects. If stubs are used to target branches, clearly mark the result stub-scoped and also run with original dependencies before claiming support. Test global/object alias cases one at a time (especially selected pointer alias with default pointer, `P+0x5F`, `P+0x10`, `P+0x20`, and indirect `+0x3B/+0xA8`) or state the explicit disjoint-RAM contract.
6. **Fault and negative controls.** Capture original fault behavior for null selected pointers, null/invalid selected state objects, invalid global service pointers, and unreadable state fields; do not substitute “defined C++ null behavior.” Controls should omit each common prewrite, invert selector normalization, change `+0x10` literal, use wrong `r2` predicate, alter state 4/5 returns/calls, skip/reset the wrong `+0x2E` write, change an `0x0028E974` argument or stack word, reverse query order, alter six-loop bounds/stride/store width, change `P+0x35` branch, or suppress the selector-19/byte-9 optional calls. Verify each mutation is actually applied and detected.
7. **Caller composition.** Compose every direct caller after argument/setup inspection, prioritizing `0x00221168` and the H2 path. For `0x00221168`, retain original upstream getter/callback code and controlled valid globals; compare callback raw result, helper call sequence/state writes, and wrapper continuation. Separately exercise actual callback-selected states and both incoming-r2 branches, but label synthetic cases as such. The run-002 observed nested target/return can guide one scenario; it cannot label that scenario as the captured internal branch unless entry arguments and branch PC are captured. Other 21 callers require their own setup and visible continuation checks before general caller support is claimed.
8. **Interworking and integration gate.** Before runtime, verify compiled entry/call state (bit 0 for Thumb function pointers where applicable), ARM/Thumb branch targets, stack alignment, and offline differential plus caller composition. If runtime is needed, use the project autonomous GDB/RSP scenario and compare the defined original/patched H2 execution. Do not call a fit, isolated pass, or one scenario whole-game equivalence.

## Commands, results, and blockers

Read-only static commands used (all exited 0):

- Capstone disassembly of image bytes at mapped ARM address `0x00286928` for the pinned 820-byte span.
- Capstone disassembly of `0x00221168..0x002211F4` to confirm its final helper call setup.
- Python aligned ARM BL-immediate target scan over `code.bin`, mapped candidate sites to `config/functions.csv` function spans.
- SHA-256/length calculation for pinned image, 820-byte function slice, and source TU.

No candidate was compiled and no differential or caller tests were run. Size fit, complete C++ behavior, all 22 call-site argument contracts, dynamic branch cause, and full runtime behavior therefore remain unverified. No concrete semantic counterexample to the static branch map was found; the principal blocker is absent full implementation/compiler evidence and incomplete caller/callee domain coverage.

## Implementation differential corrections

The first bounded C++ differential exposed additional contract errors against the pinned function, so the earlier independent contract approval must not be read as approval of these items. The comparison covered selectors `0..20`, `0x80000000`, `0xFFFFFFFF`, both incoming-r2 values, states `0,1,3,4,5,6`, and directed alternate seeds under fixed call stubs. The corrected facts are:

- Raw selector 11 writes mode 1 at `P+0x5E`; selector 13 also writes 1, while 14/15 write 0.
- Raw selector 19 selects the special pointer `*(u32*)(0x0043E188+8)` while retaining normalized selector 19. It does not select the default pointer.
- The first `P+0x2D` byte is 1 for raw selectors 13 and 15 (the selector setup changes `r2` to 1); other selector setups write zero.
- For incoming `r2==0` with `P+8!=0`, the function sets `P+0x2E=1`, calls `0x002B8D24(P, byte[P+9])`, sets `P+8=3` and `P+0x35=0`, and returns zero. It skips the update loop.
- Both `0x0028DF54` call sites pass the 32-bit word loaded from `P+0x18`, not the address `P+0x18`.

The candidate was adjusted to these observed paths. Its 296-case stub-scoped differential currently passes with an 812-byte body and 22 relocated ARM calls. This is implementation-discovery evidence, not an independent review or real-callee/caller equivalence claim. The independent contract reviewer should recheck these corrections against the pinned assembly before production integration.
