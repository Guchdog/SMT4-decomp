# 0x0029F278: stateful two-axis cursor updater

## Scope and recommendation

This is a 1536-byte ARM function, not a pure leaf or a one-field selection getter. Its wrapper control flow is mapped below, but the full side effects of 0x001FF3C4 and input/sound subsystems are not independently recovered here. A whole-function C++ conversion is reasonable only with a harness capable of executing or accurately tracing its original dependencies, including the two-result ABI of 0x002C615C and global writes. Do not promote a partial branch implementation as the full function. The current `tools/h2_calc_experiment.py` intercepts 0x0029F278 itself, so its caller fixtures do not execute or establish equivalence of this body.

## Inputs, output, ABI and observable scope

Inputs: r0=cursor object, r1=32-bit sound-enable flag. Read byte cursor+0x62; if nonzero, return 0 immediately after the prologue/epilogue without calls or object/global writes. For enabled cursor, return 1 exactly when either of two movement indicators is nonzero, otherwise 0. When returning 1, call 0x002BC200(0x0100016C) only if original r1 !=0, then return 1 regardless of sound callee return. Direct function accesses use r4 and cursor offsets through +0x62, plus stack; it calls only direct ARM BL (no indirect branch or explicit VFP operation in this wrapper). It pushes r0,r1,r4-r8,r9/sb,r10/sl,r11/fp,LR and allocates 12 more bytes (56 total); restores r4-r11/SP and returns via PC assuming conforming callees. r0-r3/r12/CPSR and callee effects remain caller-saved; no claim of preserving VFP state across callees. Object pointers, global addresses and dependency domains must be valid; no object null check or synchronization exists.

Axis subobjects are at cursor+0 and +0x28. Relevant per-axis fields are word flags +0, byte query IDs +4..+0x0B, signed-compared word +0x10, movement threshold +0x18, word +0x1C, position/base +0x20 and offset +0x24. Shared fields are word +0x50, previous combined positions +0x54/+0x58, halfword bitsets +0x5C/+0x5E, byte status +0x60/+0x61, and disable +0x62. These offsets/reads are established, semantic names only convenient interpretations. Arithmetic is ARM modulo 2^32 and comparisons at explicit BLT/BGT/BLE instructions are signed.

## Ordered control flow

1. At 0x0029F294..D4 the code performs the observable axis +0x24/+0x20 reads, saves the first axis +0x20 and second axis +0x20, initializes movement flags r8/fp=0, then calls `0x002D5618(20,20,20,20)`. Original helper writes byte 1 at 0x00465288 and halfword 20 to 0x0046527A/7E/82/86, in that order.
2. If signed cursor+0x18 >1, call 0x001FF3C4(cursor) and convert its nonzero result to first movement flag. Snapshot cursor+0x24 in stack and +0x20 in sb, read axis widths (including otherwise discarded first +0x10), and call 0x002C615C(cursor+0x50 word, second-axis+0x10 word), consuming r0. If signed sb >= r0 call 0x002892C0(cursor,r0). If first movement flag was zero and the previously saved first +0x20 differs from sb, set it to 1. The comparison is against the pre-clamp sb, not a reread after 0x002892C0.
3. If signed second-axis+0x18 >1 call 0x001FF3C4(cursor+0x28), recording nonzero as second movement flag. Then call 0x002D5644(), which writes byte 0 at 0x00465288 and halfword 0x2D to 0x0046527A/7E/82/86. Read second-axis +0x24 and +0x20, call 0x002C615C(cursor+0x50, saved second-axis+0x10), and retain its r1 as sl. This is a two-output machine ABI, not a single-return generic C++ divide declaration; helper semantics and zero divisors must not be guessed.
4. At 0x0029F3B0..43C, if sl!=0 and signed total cursor+0x50 <= `((saved first +0x24 + sb)*saved second width + current second +0x20)` modulo 2^32, adjust second axis. If current second +0x20 equals saved original second +0x20 +1, query 0x002BFFBC on cursor+0x2C then, only if zero, +0x30; if either nonzero and bit 2 of second-axis flags is set, call 0x002892C0(second axis,0). Otherwise call 0x002892C0(second axis,sl-1). Branch order and original unmasked bytes matter.
5. At 0x0029F43C..0x0029F610 run two loops of four iterations, one per axis. For first axis, query bytes +4+i and +8+i at 0x0029F454 and 0x0029F46C; for second axis, +0x2C+i and +0x30+i at 0x0029F540 and 0x0029F558. Each byte equal to 0x20 skips its own call; otherwise invoke 0x002C17D4(byte). The second query is still performed when the first is nonzero, unless its byte is 0x20. OR the truth of both results. Based on the *first* byte, set or clear the corresponding bit in halfword +0x5C or +0x5E: ID 5 -> bit 0, 6 -> bit 1, 4 -> bit 2, 3 -> bit 3; other first IDs do not alter the bitset. Stores occur once per recognized ID per iteration even if unchanged; duplicate IDs make iteration order observable.
6. At 0x0029F614..0x0029F700 recompute first combined position from +0x20/+0x24 (conditional disabled checks reread +0x62), clear +0x60, inspect +0x5C and compare current and saved +0x54 at the relevant signed boundaries, conditionally set +0x60=1, then store current combined value to +0x54. The direction groups tested are masks 0x5 and 0xA; conditional ARM flags and rereads are observable if memory changes. 0x0029F700..0x0029F84C similarly processes second-axis combined position, +0x5E, +0x61 and +0x58, including a special sl!=0 boundary case at 0x0029F7EC..848 that can clear +0x61. Preserve all signed compares and exact code paths; do not infer physical direction names.
7. At 0x0029F84C store second combined value to +0x58, OR the two movement flags and return 0 if both zero; otherwise conditionally issue sound as described and return 1. The routine is not transactionally atomic: global and cursor writes occur before later checks and dependency calls.

The original 0x001FF3C4 is itself 1104 bytes and mutates axis/input state and calls 0x00254CA8; original 0x002892C0 adjusts +0x20/+0x24. The movement helper, division helper, input queries and sound must remain original for a meaningful composed test, or be replaced by precisely controlled and separately validated stubs. Callee internal writes and any indirect/VFP operations are outside this wrapper audit. The two 0x002D56xx globals are shared and need controlled fresh fixtures; their paired calls are not equivalent to a local save/restore of arbitrary initial state.

## H2 path and caller census

`TitleConfig_Calc` state 1 reaches 0x001EADA0 with r0=work+0xE8 and r1=1; nonzero return triggers cursor-dependent display refresh, zero follows the next selection/input logic. The four query PCs and skip/consume behavior are detailed above. The title initializer passes cursor setup arguments `(3,3,1)` and stack `(0,1)` according to the frozen seam report; this does not establish every dynamic field invariant or actual physical input mapping.

The pinned-image word-aligned raw ARM scan found 55 BL and one B candidate, with no assertion that data false positives, Thumb, indirect or dynamic callers are covered. Ledger ownership below does not establish runtime reachability.

| Branch | Ledger function | PCs |
| --- | --- | --- |
| BL | `Camp_MainProc` / `0x0017FE9C` | `0x00180734`, `0x00180D84`, `0x001814A4`, `0x00181E54`, `0x00181F04`, `0x00182CC4`, `0x00183634`, `0x00184CE0`, `0x00184D90`, `0x001857B0` |
| BL | `engine_func_0018844c` / `0x0018844C` | `0x00188A18` |
| BL | `camp_func_0018a2e0` / `0x0018A2E0` | `0x0018A724` |
| BL | `script_vm_func_0018b878` / `0x0018B878` | `0x0018BC88` |
| BL | `camp_func_00195044` / `0x00195044` | `0x00195228`, `0x001952C4` |
| BL | `Camp_DrawStereoViews` / `0x0019A3EC` | `0x0019A950`, `0x0019ADA4`, `0x0019B474`, `0x0019B894`, `0x0019BB58`, `0x0019BC40`, `0x0019BE08`, `0x0019C694`, `0x0019C7E4`, `0x0019CC3C` |
| BL | `camp_func_001a1e7c` / `0x001A1E7C` | `0x001A22C4` |
| BL | `script_vm_func_001afb08` / `0x001AFB08` | `0x001AFCCC` |
| BL | `FlowScript_EvalStateControl` / `0x001C3ED4` | `0x001C46DC`, `0x001C4D84`, `0x001C5894` |
| BL | `StatusDown_CalcTaskCallback` / `0x001CA648` | `0x001CABB0`, `0x001CADBC`, `0x001CB224`, `0x001CB408`, `0x001CB520`, `0x001CB76C`, `0x001CBBC4`, `0x001CBE88`, `0x001CBF58`, `0x001CC0E4`, `0x001CC1AC`, `0x001CC454` |
| BL | `Ui_StatusScreenSkills` / `0x001CE98C` | `0x001CEF6C`, `0x001CF2C8` |
| BL | `script_vm_func_001ea928` / `0x001EA928` | `0x001EADA0` |
| BL | `script_vm_func_002041f4` / `0x002041F4` | `0x00204748` |
| B | `shop_func_002335a4` / `0x002335A4` | `0x002335B8` |
| BL | `camp_func_00329404` / `0x00329404` | `0x00329698`, `0x00329708`, `0x0032991C` |
| BL | `Camp_SubModeProcess` / `0x0032CB08` | `0x0032DDA8` |
| BL | `camp_func_0033138c` / `0x0033138C` | `0x00331464` |
| BL | `Camp_WhisperSkillTransfer` / `0x00332100` | `0x003334F8` |
| BL | `camp_func_0039779c` / `0x0039779C` | `0x00397BD8`, `0x00397BE8`, `0x00397C60` |

## Evidence needed for conversion

Add a dedicated non-leaf ARM differential harness rather than relying on the existing cursor stub. First test disabled short circuit and enabled unchanged cursor, both axes separately and together, +0x18 thresholds 1/2, sound flag zero/nonzero, saved/base and clamp differences, signed boundaries, remainder zero/nonzero, total equality, wrap and fallback 0x2BFFBC/flag cases. For each of four input sites cover byte 0x20 skip, first/second hits, zero results, duplicate IDs and recognized/unrecognized IDs; compare full 0x64 cursor, global 0x00465278 region, ordered stores, full call PC/arguments/results, return, r4-r11/SP and fault behavior under explicit mappings. Negative controls must catch missing global reset, wrong sentinel, second-query short circuit, swapped bit mapping, omitted boundary, wrong two-register division and sound gating. Compose the original state-1 caller with real dependencies and identical input fixtures; preserve any controlled stubs and their limits. Add support for original helper calls, dual r0/r1 return and dependent memory effects before claiming complete whole-function conversion. Runtime input timing/physical mapping, fault/alias/concurrency cases, malformed or zero-divisor state and full game equivalence remain unproven.

The branch map above is static evidence, not a proved complete high-level contract for 0x001FF3C4 or the sound/input systems. No compiler, ARM execution, emulator or guest input mutation occurred here.

## Provenance

All declared packet input hashes were recomputed and matched. Pinned `extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; wrapper/caller source `src/engine/leaf_batch46_b.cpp` `12d5e4a07d522a592df43a522b4004121b1c2ec7ff0131a940ac26db2f5c99cc`; current caller runner `tools/h2_calc_experiment.py` `f70429ef3cb9e186bb5d78863aade9e1d8e4a4262108bba33c48c334b8b71aac`. Read-only Capstone disassembly, ARM branch scan and hash checks exited 0.
