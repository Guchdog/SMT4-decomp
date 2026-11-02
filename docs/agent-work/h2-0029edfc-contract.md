# 0x0029EDFC: cursor update contract

## Recommendation

A bounded typed C++ wrapper is a useful H2 slice, provided 0x002892C0 remains the original tail dependency until independently supported. The exact normal returns differ by branch, and caller-visible state includes the helper's writes. Treat the object and input field names below as offset-based observations; their full UI semantics are not established. The 80-byte span, existing `void` declaration and non-leaf tail branch require focused ABI, linkage, ARM interworking and placement checks.

## Pinned ARM behavior

At entry r0=object address, r1=requested 32-bit index. Push `{r4,r5,r6,lr}` (16 bytes), preserve the inputs, and load unsigned byte object+0x62. If the byte is nonzero, return that exact byte in r0 without any object write or callee call. If zero, read object+0x24 then +0x20 as 32-bit words, add modulo 2^32, compare the result to original r1, and only if different store byte 1 at object+0x60. If equal, leave that byte unchanged, not necessarily zero. The comparison uses the unadjusted index. Restore r4-r6/LR and tail-branch ARM B from 0x0029EE44 to **0x002892C0** with r0=object and r1=original index; this means the helper returns directly to the original caller. Pinned helper returns 1 on its normal paths. The wrapper and helper preserve SP and r4-r11; caller-saved registers and condition flags can change. Neither uses VFP. Object pointer must be valid even in disabled branch; no null guard exists. No direct global or non-stack write occurs except conditional +0x60; helper writes are part of the composed behavior.

## Tail helper 0x002892C0

The original 0x002892C0 is ledger `matching`; this is a classification, not runtime equivalence for a future replacement. It reads signed-word-like count at +0x1C. If the word is zero, it writes zero at +0x24 and then +0x20, and returns 1. Otherwise it compares the requested index using ARM signed conditions: index <= 0 becomes 0; if positive and count < index, index becomes count-1 (strict comparison: index equal to count is not changed). It computes d=index-[object+0x20] modulo 2^32 and treats d as signed for its branch: if d<0 it stores index to +0x20 and zero to +0x24; otherwise it reads visible value +0x10, stores d at +0x24, signed-clamps that visible value to count when visible > count, computes limit=count-visible modulo 2^32, and if signed d>limit stores limit to +0x24 and index-limit to +0x20. It returns 1. Arithmetic is ARM 32-bit wraparound; do not use undefined C++ signed overflow to imitate edge cases. No bounds validation or generic invariant establishes positive count/visible capacity. Preserve ordered stores and do not clamp the wrapper's comparison before setting +0x60.

## H2 and other callers

At 0x001EAEA4 in `TitleConfig_Calc` state 1, after selection query 0x0029F248(work+0xE8), the original loops handled=0..2 and skips the selected index. When 0x0029D8FC(sign-extended work halfword at +0x14+2*handled) returns 6, it calls 0x002B91C4, then 0x0029EDFC(work+0xE8, handled). It ignores r0, reloads work, and queries the cursor for subsequent display. The initializer 0x002F4DB0 calls 0x0029FAE8(work+0xE8,3,3,1,0,0). That establishes setup arguments, not complete runtime object contents or the index bounds of all callers. The actual table/selection invariants and original input timing remain unproven.

A raw aligned ARM branch scan of the pinned image found 60 BL and one B candidate, no exact aligned pointer. The grouped sites below can include data false positives; Thumb, register-indirect and runtime-generated callers are outside the scan. Ledger names are attribution, not execution proof.

| Branch | Ledger function | PCs |
| --- | --- | --- |
| BL | `Camp_MainProc` / `0x0017FE9C` | `0x00181060`, `0x0018110C`, `0x00181E84`, `0x00184D10` |
| BL | `script_vm_func_00189b24` / `0x00189B24` | `0x00189E10`, `0x00189E74` |
| BL | `camp_func_0019931c` / `0x0019931C` | `0x001993CC`, `0x001993FC`, `0x00199580` |
| BL | `Camp_DrawStereoViews` / `0x0019A3EC` | `0x0019A4A4`, `0x0019A4D4` |
| BL | `FlowScript_EvalStateControl` / `0x001C3ED4` | `0x001C4B50`, `0x001C4B94`, `0x001C4BC8`, `0x001C4C84`, `0x001C563C`, `0x001C5680`, `0x001C56B8`, `0x001C58E4`, `0x001C7CF0` |
| BL | `StatusDown_CalcTaskCallback` / `0x001CA648` | `0x001CAD58` |
| BL | `script_vm_func_001ea928` / `0x001EA928` | `0x001EAEA4` |
| BL | `StatusDown_PopulateItemList` / `0x001EE7C8` | `0x001EE8FC`, `0x001EE920` |
| BL | `camp_func_0026adcc` / `0x0026ADCC` | `0x0026AEF8`, `0x0026AFA4`, `0x0026B004` |
| BL | `camp_func_0026bc28` / `0x0026BC28` | `0x0026BDC8`, `0x0026BDE0`, `0x0026BE74` |
| B | `camp_func_0026bc28` / `0x0026BC28` | `0x0026BE94` |
| BL | `camp_func_0026d910` / `0x0026D910` | `0x0026DA60`, `0x0026DA78`, `0x0026DA98`, `0x0026DAF4`, `0x0026DB1C`, `0x0026DBA8`, `0x0026DBC0`, `0x0026DBE0` |
| BL | `Camp_Calc` / `0x0028AB8C` | `0x0028B590`, `0x0028B628`, `0x0028B7A4`, `0x0028B7FC`, `0x0028B86C`, `0x0028B908`, `0x0028B9E8` |
| BL | `script_vm_func_00290544` / `0x00290544` | `0x002905F4` |
| BL | `camp_func_00293a84` / `0x00293A84` | `0x00293BAC`, `0x00293BC4` |
| BL | `engine_func_0029a03c` / `0x0029A03C` | `0x0029A228` |
| BL | `camp_func_0029e48c` / `0x0029E48C` | `0x0029E520` |
| BL | `camp_func_002a02c8` / `0x002A02C8` | `0x002A0360` |
| BL | `camp_func_002eff60` / `0x002EFF60` | `0x002F008C`, `0x002F0140` |
| BL | `StatusDown_SelectLastPartySlotAndEnterState11` / `0x002F6620` | `0x002F6678` |
| BL | `StatusDown_OpenCategorySelect` / `0x00311494` | `0x003115C8` |
| BL | `script_vm_func_00311618` / `0x00311618` | `0x00311690` |
| BL | `camp_func_00329404` / `0x00329404` | `0x0032968C` |
| BL | `camp_func_003991c4` / `0x003991C4` | `0x003994A4`, `0x003994F8`, `0x0039956C` |

## Validation and limits

Direct ARM differential on controlled valid objects should cover +0x62 values 0,1,0x80,0xFF; equal and unequal sums, modulo wrap, retained preexisting +0x60, helper zero-count, positive count/index boundaries including count-1/count/count+1, negative index, visible >count and representative signed/overflow edges on mapped memory. Compare exact r0, r4-r11/SP, all object bytes and ordered writes, including helper tail entry and r0/r1. Use mutation controls for incorrect disabled return, clearing +0x60, comparing a clamped index, wrong helper target/arguments, signed/strict boundary and missing helper stores. Test real original helper composition rather than only a stub; compose the original TitleConfig_Calc touch branch with same fixtures, including selected-row skip. Check compiler ABI and interworking and independent review before promotion, then integrated original-versus-patched runtime. Invalid pointers, data races, arbitrary alignment/fault behavior, malformed objects and runtime game behavior remain unsupported until separately established.

This is static evidence only: no compilation, differential, caller execution or runtime was performed.

## Provenance

All prepared input hashes matched at analysis time. Pinned `extracted/exefs/code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; wrapper source `src/engine/leaf_batch34_b.cpp` `603c8ced2d641cb71dd9d2bf514d86e2fa1c03f9b59b7a8b4063974a9cd52962`; caller source `src/engine/leaf_batch46_b.cpp` `c76ab50c12589404ca81e35373c8b136c50c91eb63c5af805bf05cc44c6081c7`. Read-only Capstone and aligned image scan plus input hash checks exited 0.
