# 0x002b8d24: static selector and dependency contract

Reference: code.bin SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; original ARM function 0x002b8d24, 360-byte span, 19-entry absolute ARM jump table at 0x002b8d38..0x002b8d80. Source `src/engine/leaf_batch46_a.cpp` is packet-pinned; ledger is `matching`. Static disassembly only; no compilation, guest execution or emulator. Facts below concern ordinary aligned target memory and raw registers; names of higher-level structures are not established.

## ABI and exhaustive selector map

Entry r0=obj, r1=index interpreted as an **unsigned 32-bit** value. Prologue saves r4-r6/lr, copies obj to r5 and uses `cmp r1,#0x13; ldrlo pc,[pc,r1,lsl #2]`; any unsigned index >=19 returns directly with r0=obj. Negative signed inputs have their unsigned representation and also take this path. r4-r6, SP and caller LR are restored. Case 6 uses VFP s0 as a caller-clobbered register and requires VFP availability. All target table entries are word-aligned even ARM addresses.

| Index | Table target | Observable local path and raw r0 on return |
|---|---|---|
| 0,13,14,15 | 0x002b8d34 | Immediate pop/return, r0=obj, no body writes/calls. |
| 1,10 | 0x002b8e04 | Tail ARM B to 0x002af854(obj+0xc4,2,0); returns that callee's r0. Its reviewed contract returns obj+0xc4. |
| 2,3,4,5,16,17,18 | 0x002b8d84 | BL 0x002af854(obj+0xc4,2,0), then BL same on obj+0x1dc; tail B 0x001384f0(obj+0x150,0). Pinned tail writes byte zero at obj+0x1d5 and leaves r0=obj+0x150. |
| 6 | 0x002b8db4 | Load word at obj+0xe4 into s0 and transfer raw bits to r0; compare with 0x3f800000. If unequal return **those bits** unchanged, no call. If equal tail B 0x002af854(obj+0xc4,2,0), returning its r0. This is bitwise equality, not C++ floating-point comparison. |
| 7,8,9 | 0x002b8ddc | BL 0x002af854(obj+0xc4,2,0); tail B 0x002af854(obj+0x40c,2,0), returns that callee's r0 (reviewed contract obj+0x40c). |
| 11 | 0x002b8e18 | BL 0x002bf030(obj+0xc4,7), then BL same on obj+0x268; tail B 0x001384f0(obj+0x380,0), writes byte zero at obj+0x405, returns obj+0x380. |
| 12 | 0x002b8e40 | For i=0..4, if byte obj+0x37+i is nonzero, BL 0x002af854(obj+0x498+140*i,5,0). After loop store 32-bit zero at obj+0x28 and return 0. |

Case-specific functions and tail branches execute in the caller's state at the exact instruction sequence; returns of each prior BL are discarded. Direct local effects are those stated above; 0x002af854 and 0x002bf030 can have additional reads/writes. Object, subobjects, +0xe4 word, +0x28 word, and all derived pointer arithmetic must be valid and correctly aligned for accessed ARM instructions; the index 12 loop only accesses a subobject when its flag is nonzero. No blanket null safety exists. C++ null arithmetic, memory-object lifetimes, aliasing and unsigned address wrapping must not be handwaved away. Additional side effects from each helper must be included in comparisons, and individual callee faults cannot be treated as successful returns.

## Direct callees and unresolved state

- `0x002af854`: existing production C++ with bounded differential record `docs/function-records/0x002af854.md`. Reads subobject+0x58; null returns the subobject unchanged. Otherwise updates +0x5c/+0x5e/+0x87/+0x8a/+0x60/+0x20 using entry list and index stride 12. Its current source/compiled implementation is supported for valid ordinary RAM with disjoint list/modified fields and non-overflowing index; write order differs from original. Full semantics and invalid-pointer behavior are not inferred here.
- `0x002bf030`: pinned ARM body, 120 bytes, receives r0=subobject and r1=7 in this caller. It reads pointer at subobject+0x48, dereferences halfword +8 without a null guard, uses a fixed multiplier/loop to select a pointer from the table at +0x1c, then tail branches to ARM 0x00138934. At 0x00138934 the selected pointer is stored at subobject+0x78 and, if nonzero, further halfword/byte stores and reads occur. Full table-count semantics, all paths and callee effects were not audited here. Retain the original dependency or characterize it separately; a simplistic stub is bounded evidence only.
- `0x001384f0`: two ARM instructions `strb r1,[r0,#0x85]; bx lr`; for r1=0 tail sites clear the two bytes given in the table and preserve raw r0. It is an ARM target, not an SVC instruction.

Caller 0x00286928 passes its selected object and `obj[9]` as r1 at 0x00286a10-18 and then writes obj[8]=3 and obj[0x35]=0. The jump-table input there is a u8, but the helper's own public raw ABI compares the full 32-bit r1. Other callers may pass different values and should be mapped separately. Its caller tail paths may observe the raw r0 if they use it; no public `void` declaration suffices to ignore that register.

## Differential and composition plan

Use whole compiled C++ against the pinned original for all selectors 0..18 plus 19, 0xffffffff and boundary 0x80000000, not merely H2's selected branch. Verify r0, SP, callee-saved r4-r11/d8-d15, target ABI/ARM state and VFP handling, ordered calls/arguments, branch-specific caller-clobbered outputs where actual callers use them, writable memory and faults. Vary list null/non-null, valid entry data, independent r2/r3, sentinels, and selector 6 raw bits `0x3f800000`, adjacent bits, zero, negative zero, infinities and NaNs (bitwise behavior); set r0's floating bit result explicitly in the candidate contract. For selector 12 use all 32 flag patterns with representative subobject/null-list configurations and check the five derived offsets, call count, +0x28 zero and return. Selector 11 must use real bf030 with controlled valid tables or explicitly document stub semantics; verify both calls and final byte.

Use at least two reproducible randomized memory seeds and direct original-vs-compiled comparisons, exhaustive table assertions, and negative controls: missing case, swapped target, treating selector 6 comparison as numerical float or discarding its nonmatching raw r0, wrong second subobject, skipping final byte, wrong index-12 stride/loop bound/flag, and unchanged +0x28. Check control application and detection. Include real 0x00286928 composition in both r2!=0/state paths where it calls this function and H2-reachable selectors; preserve unchanged original dependencies and distinguish synthetic fixtures from observed game states. Before production, independently review, verify ARM/Thumb interworking and caller composition offline, then compare the defined paired H2 scenario using the project runtime gate.

The existing 0x002af854 runner composes original 0x002b8d24 table index 2, verifies two callee entries and compares effects; it does not validate this helper's other table entries or a new full candidate. A conversion cannot be promoted solely from that one case or a slice. Return values, local tails and underlying helper dependencies must remain represented across all selectors.
