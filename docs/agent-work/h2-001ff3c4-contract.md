# Static ARM contract: `0x001FF3C4` cursor-axis mover

**Scope:** Pinned ARM instruction and caller-contract recovery only. No candidate, compile, emulation, or semantic-equivalence claim.

## Identity and ABI

The pinned image `extracted/exefs/code.bin` has SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The target is the 1,104-byte ARM body at `0x001FF3C4`; its byte-span SHA-256 is `dcc27aeb93ecdbbc65995089e6180f9b1a8f5216ba6969793c0e57d77ba3963e`. The matching ledger entry points to its preserved ARM body in `src/engine/leaf_batch43_a.cpp` (source SHA-256 `5ca7486aaa1244ae5e95b9e5073a7f1c49d1568cd6ad01139bc14bd86c0c0726`). The recovered behavior below comes from Capstone disassembly of the pinned bytes, not from treating the source label or ledger classification as semantic proof.

Entry is ARM state and takes one pointer in `r0` to a 0x28-byte axis record. `r1` and `r2` are overwritten before use. It returns a status in `r0`: observed status values are 0 through 4; callers inspected here test only zero/nonzero. The prologue saves `r4-r8`, `r9/sb`, `r10/sl`, `r11/fp`, and `lr` (36 bytes), then allocates 12 local bytes, for 48 bytes total. It restores `sp` and all saved callee registers before returning through `pc`. Locals at entry-SP minus 40, 44, and 48 hold query results. It uses no VFP instruction itself. Its direct callee uses VFP and preserves `d8`; caller-saved GPR/VFP state is not a preservation guarantee.

The record layout established by its loads/stores is:

| Offset | Instruction-level use |
|---:|---|
| `+0x00` | 32-bit flags; only bit 0 is changed, bit 1 triggers its initialization, bit 2 gates flag clearing |
| `+0x04..+0x07` | Four unsigned query-ID bytes, passed as first IDs |
| `+0x08..+0x0B` | Four unsigned query-ID bytes, passed as second IDs |
| `+0x10` | 32-bit width/visible span used in signed comparisons and arithmetic |
| `+0x14` | 32-bit lower/start boundary used in signed comparisons |
| `+0x18` | 32-bit threshold and, at the caller, an update-enable gate |
| `+0x1C` | 32-bit item/count boundary |
| `+0x20` | 32-bit current index/position |
| `+0x24` | 32-bit offset/scroll value |

“Width”, “start”, “threshold”, and “index” are descriptive roles, not externally proven game concepts. `LDRB` makes query IDs unsigned. The explicit `CMP`, `BLT/BGT/BLE/BGE`, `MOVLT/MOVGT`, and `CMN` decisions are signed ARM conditions; `ADD`/`SUB` arithmetic wraps modulo 2^32. The object and any transitively read globals must be mapped and readable. There is no null check: null faults at the initial `LDR [r0]`.

## Ordered query trace and flag effects

Before the movement branches, the routine performs all ten direct calls, in this order, to `0x00254CA8(r0=id0, r1=id1, r2=mode)`. Each result is reduced later by a compare-to-zero; calls are not skipped based on earlier results.

| Sequence | ID byte offsets | Mode | Saved result |
|---:|---|---:|---|
| 1 | `(+4,+8)` | 0 | local `[sp]` |
| 2 | `(+5,+9)` | 0 | `r8` |
| 3 | `(+4,+8)` | 2 | `r6` |
| 4 | `(+5,+9)` | 2 | `sl` |
| 5 | `(+4,+8)` | 1 | `sb` |
| 6 | `(+5,+9)` | 1 | `r7` |
| 7 | `(+6,+10)` | 2 | `fp` |
| 8 | `(+7,+11)` | 2 | local `[sp,#4]` |
| 9 | `(+6,+10)` | 1 | local `[sp,#8]` |
| 10 | `(+7,+11)` | 1 | later retained in `r1` |

At entry, if flags bit 1 is set, the routine sets bit 0 and writes the flags word. In the first mode-0 movement branch only, it may then clear bit 0: for pair `(+4,+8)`, bit 2 set clears it; otherwise it preserves bit 0 exactly when wrapped `offset + index - count == 0xFFFFFFFF`, and clears it otherwise. For the next mode-0 pair `(+5,+9)`, bit 2 set clears it; otherwise it preserves bit 0 only when wrapped `offset + index == 0`, clearing it for any other sum. Other fallback paths do not perform these flag-clear sequences. Bit 1 and bit 2 are preserved. A zero status does not imply no writes: flag normalization and the special offset path can write before returning zero.

## Movement decision tree

Let `A0/A2/A1` denote the saved calls for bytes `(+4,+8)` in modes 0/2/1; `B0/B2/B1` denote `(+5,+9)` in modes 0/2/1; `C2/C1` denote `(+6,+10)` in modes 2/1; and `D2/D1` denote `(+7,+11)` in modes 2/1. All predicates below mean the exact `result != 0` branch. Calls have already happened before this tree.

1. **`A0` primary path (status 1):** apply the first bit-0 clearing rule above. If signed `count <= 1`, return 0. Compute `threshold = max_signed(1, width - start)` and wrapped `next = index + 1`. If signed `next < threshold`, then signed `count > next` stores `next` to `+0x20` and returns 1. Otherwise, bit 0 set returns 0; bit 0 clear resets `+0x20` and `+0x24` to zero and returns 1. If `next >= threshold`, signed `width + offset < count` increments `+0x24` and returns 1. Otherwise compare signed `count - 1` with wrapped `offset + index`: if `count - 1 <= offset + index`, bit 0 set returns 0 and bit 0 clear resets index/offset to zero; if greater, store `next` to `+0x20`. Both successful cases return 1.
2. **Else `B0` primary path (status 2):** apply the second bit-0 clearing rule. If signed `count <= 1`, return 0. Set `width = min_signed(width,count)` only when `width > count`; clamp `start` to zero only when it is signed-negative. Compute wrapped `previous = index - 1`. If signed `previous < start`, first test `offset`: positive offset is decremented and returns 2; otherwise positive signed `offset + index` stores `previous` and returns 2; otherwise bit 0 set returns 0, while bit 0 clear stores `width - 1` to index and `count - width` to offset, returning 2. If `previous >= start`, positive signed index stores `previous` and returns 2; nonpositive index follows the same bit-0 test and `width-1`/`count-width` reset.
3. **No `A0` or `B0`:** if `C2` is zero, continue to `D2`. If `C2` is nonzero but `C1` is zero, return 0 immediately. With both nonzero, there is **no `count <= 1` gate**. If signed `width > count`, clamp the local width to count for reset values. The advance comparison and sum use the **original width**: if signed `offset + original_width >= count`, store `clipped_width - 1` to index and `count - clipped_width` to offset, then return 0. Otherwise store wrapped `offset + threshold` to offset; if its signed sum with original width is greater than count, replace offset with `count - original_width`. Set and return status 3. This distinction matters when width exceeds count.
4. At `D2`, a zero result continues to `A2`. A nonzero `D2` with zero `D1` returns 0 immediately. With both nonzero, signed `offset <= 0` stores zero to offset and index and returns 0. For positive offset, subtract threshold with wrap, store it, clamp a signed-nonpositive result to zero, and return 4. This branch has no count>1 gate.
5. At `A2`, zero continues to `B2`; nonzero with zero `A1` returns 0, and nonzero with `A1` plus signed `count <= 1` also returns 0. Otherwise use the forward status-1 movement algorithm (without the earlier bit-0 clearing rule). At `B2`, zero returns 0; nonzero with zero `B1` or signed `count <= 1` returns 0; otherwise use the reverse status-2 movement algorithm. These failed secondary gates return immediately; they do not fall through to later pairs.

For B0 and B2 reverse movement, the boundary decision is specifically ARM `SUBS previous,index,#1` followed by `BMI`/`BPL`, so it branches on the wrapped subtraction's N bit. It is not equivalent to a signed `index - 1 < 0` test for all 32-bit values: for `index == 0x80000000`, subtraction wraps to `0x7FFFFFFF` and N is clear. The ordinary signed comparisons in subsequent conditions retain their signed ARM semantics.

The exact signed branch conditions matter for negative/high-bit values and wrapped sums. The code does not clamp all inputs to conventional `[0,count)` bounds. In particular, the `D` branch can write with `count <= 1`, and the `C` branch can normalize fields while returning zero. Do not replace this with a generic list navigation routine without matching these paths.

Direct target stores are limited to the flags word and `+0x20/+0x24`; the other stores in its body are stack locals. There are no direct absolute/global accesses. Transitive query and axis services read globals and may consult input state; their state and timing are outside the target’s direct write set.

## `0x00254CA8` query service and limits

The target’s ten calls use `r0/r1` as byte IDs and `r2` as mode. The pinned 840-byte callee is a non-leaf ARM/VFP routine (span SHA-256 `efecf816aafcb6225ce4646006e54e9c3238b1c76b4ed5e0e371ee3f5cf49bfa`):

- Mode 0 calls `0x002BFFBC(id0)` and `0x002BFFBC(id1)` and ORs their results.
- Mode 1 calls `0x002B902C` for both IDs, then `0x002C17D4(id0)`; only if that is nonzero does it query `0x002C17D4(id1)`. If both latter queries are nonzero, it suppresses the second `0x002B902C` result before ORing. Otherwise the two mode-0-helper results are ORed.
- Mode 2 calls `0x002C17D4` for both IDs and ORs the results. The target uses only modes 0, 1, and 2.
- If either ID is in `12..15`, additional code may select an axis (first ID has precedence), check byte `0x00465288`, query logical IDs `14,15,12,13` in order, read signed-halfword calibration values at `0x00465278+{0,2,4,6,8,10,12,14}`, and gate one of the accumulated results using calibrated axis data. It calls `0x0027FBC8(&local_x,&local_y,0)` and the hard-float `0x002820A4` path. This is VFP-dependent input/calibration logic, not evidence of physical button names or scheduling.

The listed query helpers have bounded contracts elsewhere: `0x002BFFBC` is the counter-equals-one logical mode-1 query; `0x002B902C` is the threshold/quotient-remainder logical mode-0 query; `0x002C17D4` tests a table mask against a selected state word. Their producer cadence and physical meaning remain unresolved. `0x0027FBC8` reads calibration and sampled-axis state, can call `0x0019FE4C`, and writes the two output floats; `0x002820A4` is called with VFP arguments/results. Although their bounded function records exist, the complete live H2 service chain and input scheduling are not established. Keep them original or separately controlled in future differential tests; do not claim the target alone proves their behavior.

## Call census and H2 domain

A word-aligned ARM immediate B/BL scan of the pinned image finds three direct BL sites to `0x001FF3C4`: `0x001FEE40`, `0x0029F2E8`, and `0x0029F36C`. Disassembly confirms all three. The two `0x0029F278` call sites pass axis-0 pointer `cursor` and axis-1 pointer `cursor+0x28`, respectively. `0x001FEE40` is in `ui_func_001FE590`: after its outer flags/countdown skips, it passes `hud+0x0C`, tests only nonzero, and on movement copies axis `+0x24` to HUD `+0x64` and axis `+0x20` to HUD `+0x60`. This is another UI list-state caller, not H2. No direct ARM `BLX` target was found. Computed/indirect references and non-ARM/data misclassification are not ruled out by this scan.

For H2, `UiListCursor_Setup` at `0x0029FAE8` is called with `(cursor=work+0xE8,total=3,visible=3,cols=1,wrap=0,repeat=1)`. The pinned setup path plus `0x00296F18`, `0x00296EF8`, and `0x003170A0` initializes axis 0 with flags `6`, width `3`, final start `1`, threshold `3`, count `3`, index/offset zero, and query bytes `(+4..+11) = (6,5,32,32,15,14,32,32)`. Axis 1 has width `1`, final start `1`, threshold `1`, count `1`, IDs `(3,4,32,32,12,13,32,32)`, and zero index/offset. The initializer `0x00296F18` first writes the intermediate start value `2` to `+0x14`; the complete `0x0029FAE8` path later sets both final starts to `1`. In the wrapper, the first call is gated by signed `cursor+0x18 > 1`, so H2 axis 0 is eligible; the second is gated by signed `cursor+0x40 > 1`, so the initialized axis 1 is skipped. Both are skipped if cursor byte `+0x62` is nonzero. The wrapper passes its own `r1` sound-enable value only to its later sound call; it is not an argument to `0x001FF3C4`.

Thus the initialized H2 helper call makes all ten query calls for axis 0, with effective pairs `(6,15)` and `(5,14)` in modes 0/2/1, followed by four `(32,32)` sentinel pairs in modes 2/1. IDs `32` are outside the query helpers’ valid `0..30` domain and return zero; pairs containing `15/14` enter the `0x254CA8` special-axis path. The `0x0029F278` wrapper calls `0x002D5618` before the axis helper; the pinned wrapper contract records that call writing byte `1` to `0x00465288`, so the callee’s special-axis availability check is enabled in this initialized H2 tick. The H2 wrapper collapses the helper’s distinct nonzero statuses to a boolean movement indicator. The static setup does not prove that no other code later changes the query bytes or that a physical control produces a given query result.

## Differential fixtures and unresolved points

For a C++ conversion, reproduce the initialized H2 setup and compare the original helper directly over full 0x28-byte axis snapshots, ordered `0x254CA8` call IDs/modes/results, return status, `sp`, and `r4-r11`. Include: disabled cursor; axis thresholds 1 and 2; H2 threshold 3; count values 0, 1, 2, `INT32_MAX`, `INT32_MIN`; widths/start/indices/offsets at `-1,0,1,count-1,count,count+1` and high-bit values; flags `0..7`; wrapped `offset+index-count == -1` and `offset+index == 0`; each query pair zero/nonzero and conflicting simultaneous pairs; exact primary/fallback priority; C2/C1 cases with count 0/1 and width greater than count; and B0/B2 at index values 0, 1, `0x80000000`, and `0xFFFFFFFF` to exercise SUBS/N wrap behavior.

Stub or retain `0x00254CA8` only with an explicit test seam. For the H2 IDs, cover `(6,15)` and `(5,14)` for all three modes; ensure the `15/14` analog path is exercised with both `0x00465288` states and each of the ordered `14,15,12,13` query outcomes. Test sentinels 32 and boundary ID 30/31, mode 0/1/2, first/second-query short-circuit, and query result controls independently. Compose through the original `0x0029F278` with the pinned setup, then separately exercise the unrelated `0x001FE590` caller. Negative controls should detect reversed pair IDs, changed eager call order, mode swap, altered signed branches, changed wrap/reset condition, wrong status 3/4 path, and a skipped second axis gate. Do not claim invalid-pointer, aliasing, concurrency, physical input, scheduling, or whole-H2 behavior without separate evidence.

## Provenance and method

All 11 declared run001 packet input hashes recompute exactly. In particular, source SHA-256 is `5ca7486aaa1244ae5e95b9e5073a7f1c49d1568cd6ad01139bc14bd86c0c0726`; pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; `config/functions.csv` is pinned by the packet at `7c83607f635d3615fe0291c2509115caad402951a504c7e9cb8f7bd392df11a7`.

Read-only commands: packet hash check (`python -c ...`), Capstone ARM disassembly of pinned ranges `0x001FF3C4`/1104 bytes, `0x00254CA8`/840 bytes, `0x0029FAE8`/452 bytes, and caller windows; aligned ARM B/BL target scan; source/caller cross-checks with `rg`; all exited 0. No build, candidate, or runtime artifacts were produced. Static evidence does not establish semantic equivalence.
