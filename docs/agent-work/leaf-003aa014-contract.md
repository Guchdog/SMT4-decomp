# Contract recon: `battle_func_003aa014` (0x003aa014)

## Identity

- Original span: `[0x003AA014, 0x003AA264)`, 592 bytes, ARM.
- Source: `src/engine/leaf_batch45_a.cpp` (currently naked/raw).
- Category: `battle`.
- Reference: `extracted/exefs/code.bin`.
- Current ledger row: `0x003aa014,592,matching,battle,battle_func_003aa014,src/engine/leaf_batch45_a.cpp`.

## ABI

- `extern "C" void battle_func_003aa014(void* ctx, void* sb, int flag, int id)`:
  `r0 = ctx`, `r1 = sb`, `r2 = flag`, `r3 = id`.
- No explicit return value is computed; the function ends with the last helper
  call and restores `r4-r8/sb/sl/fp`. The caller must ignore `r0`.
- Frame: `push {r4-r8,sb,sl,fp,lr}` then `sub sp,#0x4C`; epilogue restores.

## Initial state

- `r5 = *(u32*)(ctx + 0x594)`; if `flag != 0`, `r5 += 1`.
- `r4 = ctx`, `sb = sb`, `r6 = flag`, `r7 = id`.
- `r0 = 0x2BF6C8(ctx + 0xC8, sb + (flag ? 0x42F : 0x40E))`.
- `sl = (s16)*(u16*)(r0 + 8)`, `fp = (s16)*(u16*)(r0 + 0xA)`.

## Main calls (ordered)

| # | Call | Arguments |
|---|---|---|
| 1 | `0x2BF6C8` | `r0=ctx+0xC8`, `r1=sb + (flag ? 0x42F : 0x40E)` |
| 2 | `0x22D994` | only if `flag != 0`: `r0=ctx`, `r1=sb`, `r2=r5`, `r3=(s8)ctx[0x56D]` |
| 3 | `0x22DE40` | `r0=ctx`, `r1=1`, `r2=id`, `r3=sb`, `stack[0]=flag`, `stack[4]=r5` |
| 4 | `0x22DD28` | `r0=ctx`, `r1=id`, `r2=sb`, `r3=flag`, `stack[0]=r5` |
| 5 | `0x22DC40` | same argument shape as call 4 |
| 6 | `0x2B087C(id & 0xFFFF)` | returns a record pointer or null |
| 7 | `0x22DB5C` | `r0=ctx`, `r1=(record ? record[2] : 0)`, `r2=sb`, `r3=flag`, `stack[0]=r5`, `stack[4]=0xFFFFFFFF` |
| 8 | `0x2B087C(id & 0xFFFF)` | again; `r8 = record ? *(u32*)(record+4) : 0` |
| 9 | `0x2BF6C8` | `r0=ctx+0xC8`, `r1=0x49D` when `flag != 0`, else `0x48F` |
| 10 | `0x2BE7FC` | `r0=sp+0x20`, `r1=0x00643425` (format string pointer), `r2=r8` |
| 11 | `0x230C80` | `r0=ctx+0xC8`, `r1=(flag ? 0xFBEB39FF : 0)`, `r2=sl+new_x`, `r3=fp+new_y`, stack args including `r5`, `0`, `7`, and `sp+0x20` |
| 12 | `0x2B087C(id & 0xFFFF)` | again; `r8 = record ? *(u32*)(record+8) : 0` |
| 13 | `0x2BF6C8` | `r0=ctx+0xC8`, `r1=0x4A1` when `flag != 0`, else `0x493` |
| 14 | `0x2BE7FC` | `r0=sp+0x20`, `r1=0x00643425`, `r2=r8` |
| 15 | `0x230C80` | second draw call: `r0=ctx+0xC8`, `r1=(flag ? 0x6BBB2CFF : 0)`, `r2=sl+new_x`, `r3=fp+new_y`, stack args including `r5`, `0`, `7`, and `sp+0x20` |

The constants at the literal pool are:
- `0x3AA248 = 0x0000049D`
- `0x3AA24C = 0xFBEB39FF`
- `0x3AA250 = 0x00643425` (pointer to the format string)
- `0x3AA254 = 0x000004A1`
- `0x3AA258 = 0x6BBB2CFF`
- `0x3AA25C = 0x0000048F`
- `0x3AA260 = 0x00000493`

The two `add r1,pc,#...` sites resolve to `0x3AA250`, i.e. the
`0x00643425` pointer. The `0xFBEB39FF`/`0x6BBB2CFF` words are passed as raw
32-bit arguments; treat them as opaque constants (they may be float bit
patterns).

## Branch map

- `flag == 0` vs `flag != 0` selects `sb+0x40E` vs `sb+0x42F` at call 1,
  skips call 2, selects `0x48F` vs `0x49D` at call 9 and `0x493` vs `0x4A1` at
  call 13, and selects the `r1` constant for calls 11/15.
- `0x2B087C(id)` may return null; each of the three lookups then substitutes
  zero for the loaded field (`+2` byte, `+4` word, `+8` word).
- The two coordinate additions use the first `0x2BF6C8` result (`sl`, `fp`) plus
  the second/third `0x2BF6C8` result (`s16` at +8/+0xA), stored at
  `sp+0x18`/`sp+0x1C` and `sl`/`r7`.
- No loops in the body.

## Differential plan

- Stub all helpers with hooks that log `(name, r0..r3, stack args)` and return
  deterministic values. `0x2B087C` must be switchable per id to return null, a
  record with `+2/+4/+8` values, or distinct records per call.
- Fixtures: `ctx` with `+0x594` and `+0x56D`, `sb` with the two offsets, the
  first/second/third `0x2BF6C8` outputs with signed +8/+0xA fields, and the
  format output buffer.
- Cases: `flag=0/1`; `0x2B087C` null and non-null for each of the three calls;
  signed coordinate boundaries; zero/positive/negative `r5`; both constant
  argument words; all `sb` offsets. Compare the full ordered call log (including
  stack arguments), the `sp+0x10..0x1F` draw arguments, the format buffer, and
  the return/SP/callee-saved state.
- Add negative controls for a wrong constant selection and a wrong `0x2B087C`
  field offset.

## Limits

- The called draw/format routines are stubbed; no rendering, text layout, or
  battle UI state is exercised.
- The `0x00643425` format string and the two raw constant words are treated as
  opaque; their semantic meaning is not established.
- Fixtures are synthetic; no runtime or whole-game equivalence is claimed.
