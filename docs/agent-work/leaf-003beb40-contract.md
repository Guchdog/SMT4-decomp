# Contract recon: `ui_func_003beb40` (0x003beb40)

Read-only static contract report. No source, ledger, board, or milestone changes.

## Identity and starting state

- Original span: `[0x003BEB40, 0x003BED80)`, 576 bytes, ARM, 144 decoded words.
- Pinned image: `extracted/exefs/code.bin`
  - image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`
  - function-body SHA-256: `3b4dde3b16d106ec9df73f14c0875a33448e9c87002e769cf7eb66e7ec7a9d2b`
- Current source: `src/engine/leaf_batch45_a.cpp` lines 420-497, a
  `DECOMP_FUNC(0x003beb40, 576)` naked function made of raw `.hword` words. It
  has no semantic types, parameter names, or readable control flow.
- Ledger start state: `config/functions.csv:9775` is
  `0x003beb40,576,matching,ui,ui_func_003beb40,src/engine/leaf_batch45_a.cpp`;
  `PROGRESS.md:9813` repeats the `matching` label. Any semantic rewrite whose
  bytes differ must not keep a dishonest `matching` ledger label.
- The function is not a leaf: it makes 16 direct calls and reads shared tables.

## ABI

Proposed usable prototype (AAPCS32, softfp/VFP mixed):

```c
int ui_func_003beb40(void* ctx, int id_a, int id_b, int v3, int v4,
                     float f0, float f1);
```

- Integer arguments: `r0 = ctx`, `r1 = id_a`, `r2 = id_b`, `r3 = v3`, and one
  stack word `v4` at `[entry_sp + 0]` (read as `[sp,#0x90]` after the frame is
  built). No other stack arguments are read.
- Float arguments: incoming `d0` is saved with `vmov.f64 d10,d0`, so the body
  sees two floats `s0 = f0` and `s1 = f1`; `s20/s21` are their callee-saved
  copies. `f1` is used as a multiplier; `f0` is the base value added to
  `stat*4.5`.
- Return: signed 32-bit in `r0`, produced by `vcvt.s32.f32 s0,s16` in the common
  tail (truncate toward zero, VFP saturating conversion).
- Callee-saved: prologue is
  `push {r4,r5,r6,r7,r8,sb,sl,fp,lr}` (0x24) + `vpush {d8,d9,d10,d11}` (0x20)
  + `sub sp,#0x4c`, total frame `0x90`. Epilogue restores exactly the same
  registers and `sp`; `d8-d11` (s16-s23) are preserved. `r4-r8,sb,sl,fp` are
  used as working registers. Condition flags are unspecified after return.
- The only PC-writing instruction is the final `pop {...,pc}`; no indirect
  calls or tail branches.

## Branches

Nine explicit branches, all inside the body:

| PC | Instruction / target | Condition and effect |
|---|---|---|
| `0x003BEC40` | `beq 0x003BEC70` | `row_a[0x00]` (u32 at `id_a` row) bit 1 is clear: skip the bonus path. |
| `0x003BEC50` | `beq 0x003BEC70` | `0x2AE3F0(ctx) == 0`: skip the bonus path. |
| `0x003BECDC` | `bne 0x003BED18` | `*(u32*)(ui + 0x44A0)` bit 18 (`0x40000`) set: skip the `0x23EBF0` multiplier. |
| `0x003BECF0` | `beq 0x003BED00` | `row_a[0xCC]` bit 2 clear: test target bit only. |
| `0x003BECF8` | `beq 0x003BED50` | Secondary flag bit 2 clear: use `0x23EBF0()+8`. |
| `0x003BECFC` | `b 0x003BED08` | Secondary flag bit 2 set: use `0x23EBF0()+0`. |
| `0x003BED04` | `beq 0x003BED50` | Secondary flag bit 2 clear: use `0x23EBF0()+8`. |
| `0x003BED28` | `beq 0x003BED3C` | Affinity byte `view[0x0E + row_b[0x217]] == 0`: no final affinity factor. |
| `0x003BED60` | `b 0x003BED14` | Merge the `+8` multiplier path into the common affinity tail. |

`0x003BEBA0` is a conditional VFP load (`vldrne s16`), not a branch: when
`row_a[0xCC]` bit 2 is set, the initial factor changes from `1.0` to `0.8`.

The body itself has no loops. Loops exist in callees: the 10-entry status scan
in `0x3BE898`, and the 109 x 50 table scan in `0x27DCA0`/`0x282B94`.

## Direct calls, in execution order

All targets are pinned-original addresses; order below is static order, and the
last three are conditional.

| # | Call | Argument setup | Return use |
|---|---|---|---|
| 1 | `0x293C98()` | none | `fp = ui` singleton pointer (`*[0x00435D90]`). |
| 2 | `0x27DCA0(ui, id_a)` | `r0=fp`, `r1=r6` | `r4 = id_a record` (row + `0xCC`) or null. |
| 3 | `0x27DCA0(ui, id_b)` | `r0=fp`, `r1=r8` | `r5 = id_b record` (row + `0xCC`) or null. |
| 4 | `0x22A824(8, (float)id_a)` | `r0=8`, `s0=(float)r6` | `s17 = factor_8(id_a)` (float). |
| 5 | `0x22A824(10, (float)id_b)` | `r0=10`, `s0=(float)r8` | `s19 = factor_10(id_b)` (float). |
| 6 | `0x3BE898(id_a, id_b)` | `r0=r6`, `r1=r8` | `s1 = status factor`; stored into `s17 = factor_8*factor_10*s1`. |
| 7 | `0x282B94(ui, id_a)` | `r0=fp`, `r1=r6` | `r0 = id_a row base`, passed to call 8. |
| 8 | `0x2475E4(sp+0x24, ui, row_a)` | `r0=sp+0x24`, `r1=fp`, `r2=row_a` | Fills a 0x22-byte view; first 0x20 bytes are copied to `sp+0x00`. |
| 9 | `0x22AC9C(u16 view[2], sp+0x48)` | `r0=ldrh [sp+2]`, `r1=sp+0x48` | Writes one int to `sp+0x48`; **never read afterwards (dead result)**. |
| 10 | `0x293C98()` | none | `r0 = ui` again. |
| 11 | `0x282B94(ui, id_a)` | `r0=ui`, `r1=r6` | `r0 = row_a`; tests `*(u32*)row_a & 2`. |
| 12 | `0x2AE3F0(ctx)` | `r0=sb` (incoming `r0`) | Only when `row_a[0] & 2`; `r6 = returned object`; null skips 13-14. |
| 13 | `0x2AE394(ctx)` | `r0=sb` | `r1 = count` for call 14. |
| 14 | `0x28412C(object, count, 1)` | `r0=r6` (from 12), `r1=count`, `r2=1` | `r8 = bonus`; otherwise `r8` stays 0. |
| 15 | `0x23EBF0()` | none | `s0 = *(float*)(result + 0)`. |
| 16 | `0x23EBF0()` | none | `s0 = *(float*)(result + 8)`; reached at `0x3BED54`. |

Call 14 overwrites `r6` with the `0x2AE3F0` object; the original ids are no
longer needed after that point.

## Computation (ordered)

Let `A = id_a` row, `B = id_b` row (row stride `0x288`), and let
`view = local 0x22-byte structure` filled by call 8 from `A`.

1. `s16 = (A[0xCC] & 4) ? 0.8f : 1.0f`.
2. `statA = (float)(s16)A[0x1C0]` (read as `[r4+0xF4]` with `r4 = A+0xCC`).
3. `m8 = 0x22A824(8, id_a)`; `m10 = 0x22A824(10, id_b)`;
   `status = 0x3BE898(id_a, id_b)`; `s17 = m8 * m10 * status`.
4. If `(A[0x00] & 2) != 0` and `obj = 0x2AE3F0(ctx)` is non-null:
   `bonus = 0x28412C(obj, 0x2AE394(ctx), 1)`; otherwise `bonus = 0`.
5. `s20 = f0 + statA * 4.5f`;
   `s4 = s20 * (1/3) * f1`;
   `s3 = s4 * s17 * s16 * ((float)view[8] * 0.01f)`;
   `s0 = s3 / (0.5f * (float)(v3 + v4))`;
   `s16 = s0 + 0.0f + (float)bonus`.
6. If `*(u32*)(ui + 0x44A0)` does **not** have bit `0x40000`:
   - if `B[0xCC] & 4` is clear, `s16 *= *(float*)(0x23EBF0() + 8)`;
   - if `B[0xCC] & 4` is set, `s16 *= *(float*)(0x23EBF0() + 0)`.
   The `A[0xCC] & 4` test is redundant; only the target bit selects the offset.
7. `idx = B[0x217]` (u8 at `r5+0x14B`, `r5 = B+0xCC`). If
   `view[0x0E + idx] != 0`, `s16 *= (float)view[0x0E + idx] * 0.01f`.
8. Return `(s32)s16`.

So the core arithmetic is:

```text
result = ((f0 + A.stat_1c0*4.5) * (1/3) * f1
          * m8(id_a) * m10(id_b) * status(id_a,id_b)
          * (A_cc_flags_bit2 ? 0.8 : 1.0)
          * view[8]/100)
         / (0.5*(v3+v4))
         + bonus
         [* camp_table_multiplier] [* affinity_percent/100]
```

`v3` and `v4` are sign-extended caller bytes; the callers pass
`view[0x20]` and `view[0x1F]` of their own view structure. In both known
callers the returned value is subsequently clamped to 100 and further reduced,
so this is a percentage-like/damage-like integer, not a raw object pointer.

## Global and object memory

Direct accesses in this body (no direct writes to game memory; only the local
frame is written):

| Address / object | Width | Access | Meaning |
|---|---|---|---|
| `*[0x00435D90]` | word | read | Global UI singleton pointer (`0x293C98`). |
| `ui + 0x1FC0` | word | read inside `0x27DCA0`/`0x282B94` | Pointer to unit table: 109 rows, stride `0x288`, 50 `s16` ids at row+`8`. |
| `A + 0x00` | word | read | `A` row flags; bit 1 gates the `0x2AE3F0` bonus path. |
| `A + 0xCC` | byte | read | Primary record flags; bit 2 selects `0.8`. |
| `A + 0x1C0` | signed halfword | read | Primary stat added as `stat*4.5` (`[A+0xCC+0xF4]`). |
| `B + 0xCC` | byte | read | Secondary record flags; bit 2 selects offset `0` vs `8` of the camp table. |
| `B + 0x217` | byte | read | Affinity/element index into `view[0x0E+...]`. |
| `ui + 0x44A0` | word | read | Global flag word; bit 18 disables the `0x23EBF0` multiplier. |
| `0x00439A94 + 4*(3-stat)` | float | read in `0x22A824` | Category 8/10 range/stat multiplier table. |
| `0x00439AB0 + 4*(3-stat)` | float | read in `0x22A824` | Category 9/11 variant table. |
| `0x00439AE8 + 36*index` | struct | read in `0x23EBF0` | Camp/global modifier table; this body uses `+0` and `+8` floats. Index comes from `*(u8*)(*(u32*)0x0043E2AC + 0x24BB0)`. |
| `A + 0x278/0x27C/0x280/0x284` | word | read inside `0x22AD74` | Optional status-list source pointers (unresolved selection). |
| `A + 0x72 + 2*category` | signed halfword | read in `0x22A824` | Stat for category 8 (`A+0x82`) and 10 (`A+0x86`). |
| `A + 0x8C/0x90/0x94` | signed halfword | read in `0x22A824` | Extra category-8 factors (`1.25`, `2.5`, `3.0`). |
| `A + 0x1C6` | halfword | read in `0x22A824` | Bit `0x10` forces table index 6 (`1.6`). |
| `[0x0043427C]` chain | word | read in `0x22A824` | Global flags; bit `0x200` suppresses category 7/8 extras. |

Local frame (`sp` after `sub #0x4C`):

| Offset | Contents |
|---|---|
| `0x00..0x1F` | copy of `view[0x00..0x1F]` from the view builder. |
| `0x20..0x23` | copy of `view[0x20..0x23]` (`ldr [sp+0x44]`; two bytes extend past the 0x22-byte view). |
| `0x24..0x45` | 0x22-byte view structure written by `0x2475E4`. |
| `0x46..0x47` | Unused/padding inside the reserved frame. |
| `0x48..0x4B` | dead output of `0x22AC9C`. |
| `0x4C..0x8F` | reserved frame/saved registers; `0x90` is `v4`. |

The affinity lookup `view[0x0E + B[0x217]]` has no bounds check. Valid data must
keep `B[0x217] <= 0x11` (array `view+0x0E..0x1F`); larger values read other view
fields and eventually the caller's stack frame.

## Constants and helper contracts recovered from the ARM

Main-function constants (`0x3BED64..0x3BED7C`): `0.0`, `1.0`, `0.8`, `4.5`,
`1/3`, `0.01`, `0.5`.

`0x27DCA0(ui,id)` / `0x282B94(ui,id)`: scan the 109-row table at `ui+0x1FC0`,
row stride `0x288` (`id_row*648`), 50 signed halfword ids at row+8. On match,
`0x282B94` returns `row`; `0x27DCA0` returns `row+0xCC`. No match returns null.

`0x22A824(category, (float)id)`:
- casts the float id to signed int and finds its row;
- `stat = row[0x72 + 2*category]`;
- category 7/8 uses `0x439A94[3-stat]`; for those two categories only,
  `row[0x1C6] & 0x10` substitutes `0x439A94[6] = 1.6`;
- category 10 uses `0x439A94[3-stat]` with no `row[0x1C6]` override;
- category 9/11 uses `0x439AB0[3-stat]`, and if `row[0x8A] != 0` multiplies by
  `0x439AB0[3-row[0x8A]]`;
- category 8 extras: `row[0x90]!=0 -> *2.5`, `row[0x8C]!=0 -> *1.25`,
  `row[0x94]>0 -> *3.0`;
- no bounds check on the `3-stat` index. Values 0..3 map to
  `1.0, 0.833, 0.714, 0.625`; stat 4 reads the word before the table
  (`0x78`, denormal as float), so out-of-domain stats are unspecified.

`0x3BE898(id_a,id_b)`: returns `1.0` unless both rows exist and `B[0x00]` has
bit `0x100`; then it asks `0x22AD74(A, sp)` to fill ten status ids, looks each
up with `0x2840B8(id)`, sums `u16` values at `found+0x36`, and returns
`sum * 0.01` (again `1.0` when the sum is zero). The status-source selection
inside `0x22AD74` is unresolved.

`0x2475E4(out, ui, row)`: writes a 0x22-byte view. The initializer sets
`out[8] = 100` (u16) and zeroes the rest; a switch on `row[0x218]` then selects
unit-type-specific data and overwrites fields including `+0x1F`, `+0x20`, and
`+8`. The exact meaning of each field is unresolved, but the use in this body
shows `view[8]` is a percentage-like scalar (default 100) and the bytes at
`view[0x0E..]` are an indexed affinity/element table.

`0x23EBF0()`: reads an index byte from
`*(u8*)(*(u32*)0x0043E2AC + 0x24BB0)` and returns
`0x00439AE8 + 36*index`.
This body reads floats at `+0` and `+8`.

`0x2AE3F0(ctx)`: looks up/constructs a battle object for `ctx`; the result is an
object with a `+0x38` status word and a `+0x58` array of 8 `{u8 type,u8 value}`
entries. `0x2AE394(ctx)` returns a small entry count from a table. `0x28412C`
returns zero when the object is null or `[obj+0x38] & 0x80000000`, otherwise the
sum of `value` for up to `min(count-1,8)` entries whose `type == 1`.

`0x22AC9C(id, out)`: identity-ish id mapper. It writes `id` for ids 0..7 and
9 and 11..17 (`11 -> 0x0B`), but ids 8 and 10 return without writing. Since the
caller never reads `sp+0x48`, this call is dead in this function.

## Known callers

- `camp_func_003bdcd8` at `0x003BE210`: `r0 = [sp+0x48]`, `r1 = [sp+0x78]`,
  `r2 = sb`, `r3 = ldrsb [sp+0x30]`, stack arg `= ldrsb [sp+0x2F]`. It then
  divides the result by 3 (`0x55555556` magic) when `[sp+0x2D] != 0` and clamps
  to 100.
- `ui_func_003be55c` at `0x003BE668`: `r0 = [sp+0x40]` (its incoming `r1`),
  `r1 = [sp+0x70]` (first stack argument, primary id), `r2 = r7` (second stack
  argument, secondary id), `r3 = ldrsb [sp+0x28]` (`view[0x20]`),
  stack arg `= ldrsb [sp+0x27]` (`view[0x1F]`), `s0 = (float)(u16 [obj+0x2C])`
  from the `0x2AE3F0`-style object, and `s1 = s16` (its incoming float `s0`).
  It then applies the same divide-by-3 and clamp-to-100 post-processing.

This caller evidence supports `r0 = context`, `r1/r2 = primary/secondary unit
ids`, and `r3/v4 = small signed view fields` (likely range/level-like values,
but the exact names are not proven).

## Unresolved behavior and data-layout assumptions

1. `0x2475E4` is a 1664-byte builder. Only its output contract is known:
   `view[8]` defaults to 100 and is overwritten by unit-type-specific data;
   `view[0x1F]`/`view[0x20]` are the two bytes the callers feed back as `v3/v4`;
   `view[0x0E..]` is an indexed byte table. Field names and the full switch are
   not recovered.
2. The exact status-id source for `0x22AD74` and the `0x2840B8` lookup/factory
   are unresolved. `0x3BE898` is only bounded as "sum of up to 10 looked-up
   status values * 0.01, or 1.0".
3. The table at `ui+0x1FC0` is assumed to be the 109-row x 648-byte unit table
   used by sibling functions. Row flags/fields are documented by offset, not by
   a proven struct type. `0x27DCA0`/`0x282B94` perform the lookup and return the
   record at `+0xCC` versus the row base respectively.
4. `view[0x0E + B[0x217]]` is unguarded. No valid-domain evidence is available
   for `B[0x217] >= 0x12`; treat larger values as an overread, not a behavior to
   reproduce silently.
5. `3 - stat` table indexing is unguarded; stats above 3 read outside the float
   tables. Stats below 0 also index outside the recovered domain.
6. `v3 + v4 == 0` makes the denominator zero. The original produces VFP
   infinity/NaN and then `vcvt.s32.f32`; the exact result must be measured, not
   assumed to be C++ undefined behavior.
7. `0x22A824` reads a separate global flag chain (`[0x0043427C]`, bit `0x200`)
   to suppress category-7/8 extras. That global is not identified.
8. The float pair in `d0` is a non-standard mixed integer/float signature. A
   replacement must preserve this exact register convention; a normal C++
   prototype with `float,float` after four integer arguments emits the same
   `s0/s1` convention on the target ABI, but should be verified.
9. The `0x22AC9C` call has no observable effect in this function and can be
   omitted only if the differential call log is allowed to differ; otherwise
   keep it for byte-level/call-trace fidelity.

## Proposed Unicorn differential plan

Use the existing pattern in `tools/test_leaf_0022e008.py`: compile one TU,
extract the candidate body, run pinned-original and candidate in separate
Unicorn instances with identical memory maps, and install deterministic stubs at
the exact original call addresses.

### Harness and fixtures

- Map code, a writable stack, a synthetic `ui` object, a synthetic unit table
  (`0x288` stride), a view buffer, a camp-modifier table, and a global flag page.
- Enter at `0x003BEB40` with `lr` pointing at a trap; set `r0-r3`, `[sp] = v4`,
  `d0 = {f0,f1}`, and nonzero sentinels in all callee-saved registers and
  `d8-d11` to prove preservation.
- Stub 16 call sites. Return synthetic rows/records that make the row layout
  explicit; log `(pc, r0-r3, [sp], s0, s1)` and return values for every call.
- Stub `0x293C98` with a fixed `ui` pointer; `0x27DCA0`/`0x282B94` with real
  table scans over a small but structurally faithful table; `0x22A824`,
  `0x3BE898`, `0x2475E4`, `0x22AC9C`, `0x23EBF0`, and
  `0x2AE3F0`/`0x2AE394`/`0x28412C` with scripted deterministic returns.
- Normalize stack-pointer arguments relative to the scratch frame base before
  comparing call logs.

### Positive cases

1. Baseline: both ids found, `A[0xCC]`/`B[0xCC]` bits clear, `row_a[0] & 2 == 0`,
   `view[8]=100`, affinity byte 0, `f0=10`, `f1=1`, `v3=2`, `v4=4`.
2. Primary flags bit 2 set -> initial `0.8`; secondary flags bit 2 set ->
   `+0` camp multiplier instead of `+8`.
3. `row_a[0] & 2` set with `0x2AE3F0` non-null -> bonus path; vary
   `0x2AE394` count (0, 1, 8, 9) and entry types (0/1/other).
4. `ui+0x44A0` bit 18 set -> camp multiplier skipped.
5. Affinity `view[0x0E+idx]` nonzero with values 1, 50, 99, 100, 255.
6. `view[8]` default 100 and custom 0, 1, 2000 (only if the real view can
   produce it); `f0`/`f1` zero, positive, negative, and large.
7. Category-8/10 table hits for stats 0..3 and `row[0x1C6] & 0x10` override.

### Boundary and negative-control cases

- `v3+v4 == 0` (exact zero denominator), and opposite-sign `v3/v4` summing to 0.
- Null `row_a`, null `row_b`, id not present in table, row with `B[0]` bit
  `0x100` clear.
- `B[0x217] = 0x11` (last in-array byte), `0x12` (first copied word byte),
  `0x16` (wraps into `view[0]`), and `0xFF` (overread).
- `stat = 4` (reads before table A), negative stat, and `stat > 6`.
- `0x2AE3F0` returns null; `0x28412C` sees `[obj+0x38] & 0x80000000`; count 0
  and count > 8 (clamp).
- `0x22A824` returns 0, negative, +inf-like, and NaN-like values.
- Deliberately mis-stub one helper (e.g. return 1.0 instead of 0.8) and confirm
  the harness reports a difference; this is the negative control for the stub
  wiring itself.

### Exact comparisons

For every case compare:

- `r0` (signed return value);
- final `pc` (must be the trap/LR), final `sp` (must equal entry `sp`);
- `r4-r8, sb, sl, fp` and `d8-d11`/`s16-s23` preservation;
- ordered call log with the same call sequence, same `r0-r3`/stack arguments
  and same `s0/s1` float bits where applicable;
- the entire local stack frame, especially `sp+0x00..0x47` (view and copied
  view), and the `sp+0x48` dead word;
- any synthetic table/global pages that either implementation writes (this
  body should write none outside the stack; helper stubs must be deterministic).

Explicitly exclude condition flags from equivalence and do not require identical
FP rounding beyond the compared final integer plus the documented float
arguments/results; use bit-exact float comparison for `s0/s1` at call boundaries
and a tolerance-free integer compare for `r0`.

### Caller composition

After the function-level matrix, run both known callers with the same stubs:

- `camp_func_003bdcd8` path at `0x003BE210`;
- `ui_func_003be55c` path at `0x003BE668`.

Compare the caller's post-processing (`/3` when the flag is set, clamp to 100)
and the final returned value. This catches register-convention mistakes that a
standalone target test would miss, especially the `d0 = {f0,f1}` and stack-arg
layout.
