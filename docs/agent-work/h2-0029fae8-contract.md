# H2 cursor setup contract: `0x0029FAE8`

Status: static audit of the pinned US v0.1.0 ARM body and its direct callers. No candidate, compilation, differential run, build, or emulator session was performed.

## Identity and evidence

- Entry/span: ARM-state `0x0029FAE8..0x0029FCAC`, 452 bytes (113 words); pinned `code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; slice SHA-256 `775855685fc946151107ff9a787cce85eee1ef29b839e558628ddcc3429e58b9`.
- Source mirror is the naked listing `src/engine/leaf_batch40_a.cpp` at `DECOMP_FUNC(0x0029fae8, 452)`, SHA-256 `3ebf6bb17e01ac9eb9b678f85307e7d4fcf09c83417e752b09b1dfa475dfbfe3`. Static instruction decode was from the pinned image, not from the mirror.
- The H2 title initializer calls this entry at `0x002F4DB0`. Its cursor argument is `work+0xE8`; the remaining arguments are `(total=3, visible=3, cols=1, stack_arg5=0, stack_arg6=1)`. This matches the existing initializer contract and the pinned callsite.

## ABI and register/stack behavior

The entry consumes six 32-bit arguments:

| ABI location | Body's saved value | Existing caller label (where available) |
|---|---|---|
| `r0` | `r4` | cursor pointer |
| `r1` | `r5` | total item count |
| `r2` | `sb`/`r9` | visible-row count |
| `r3` | `r6` | column count |
| `[entry_sp]` | `r7` | `wrap_row` |
| `[entry_sp+4]` | `r8` | `repeat` |

The first instruction pushes `{r3-r8,r9-r11,lr}` (40 bytes); `add r0,sp,#0x28; ldm r0,{r7,r8}` reads the two incoming stack words. Calls that need a fifth word write it at current `[sp]`, which is the called function's argument five. The body restores `r3-r11`, LR, and SP on both paths. On the early disabled path it returns raw `r0=1`. On the normal path it restores LR then tail-branches; the tail leaf preserves raw `r0=cursor+0x28` and returns to the original caller. Caller-saved flags/scratch other than this observed return are not outputs.

## Control flow and direct writes

ARM comparisons below are signed conditions (`GT`, `LE`) unless stated otherwise.

1. **Normalize the fifth argument.** If `wrap_row==0`, keep it zero. If nonzero, compare signed `cols` with 1; when `cols>1`, clear the local wrap value. Thus the alternate axis-0 ID set is selected only when the incoming fifth word is nonzero and signed `cols<=1`.
2. **Disabled/empty path.** If signed `total<=0`, set byte `cursor+0x62=1` and return `r0=1`. This path does not clear or rebuild the prior axis records.
3. **Active header and row calculation.** If `cols==1` and signed `visible>total`, replace visible with total; otherwise preserve visible. Store total at `cursor+0x50`, then clear byte `cursor+0x62`. Call `0x002C615C(total,cols)` at `0x0029FB48`; its pinned contract returns quotient in `r0`, signed remainder in `r1`. Set local rows to quotient, adding one iff signed remainder is positive. The routine does not guard zero/negative `cols`; those cases inherit the pinned divider's behavior and are not normalized here.
4. **Axis 0 record.** Call `0x00296F18(cursor,visible,rows)` at `0x0029FB6C` when normalized wrap is nonzero, otherwise at `0x0029FBC4`. The helper initializes the 0x28-byte record. Then call `0x00296EF8` to fill the first query pair and duplicate it into the next pair. For nonzero wrap, its arguments are `(cursor,6,5,3,stack[0]=4)`; for zero wrap they are `(cursor,6,5,32,stack[0]=32)`. If stack argument six (`repeat`) is nonzero, call `0x003170A0`: for nonzero wrap write `(15,14,12,13)` at `cursor+8..+11`; for zero wrap write `(15,14,32,32)` there. If repeat is zero, this second pair remains the duplicate written by `0x00296EF8`.
5. **Axis 1 record.** If visible equals 1 and signed cols is greater than 1, clamp cols to total only when signed `cols>total`, then call `0x00296F18(cursor+0x28,clamped_cols,total)` at `0x0029FC28`. Otherwise call it at `0x0029FC44` with `(cursor+0x28,cols,cols)`. Call `0x00296EF8(cursor+0x28,3,4,32,stack[0]=32)` unconditionally on the active path. If repeat is nonzero, call `0x003170A0(cursor+0x28,12,13,32,stack[0]=32)`; otherwise the duplicated pair remains.
6. **Finalize and tail-call.** Zero halfwords at cursor `+0x5C` and `+0x5E`; store word 1 at cursor `+0x14` (axis-0 start). Restore registers/LR and tail-branch to interior entry `0x002FC20C` with `r0=cursor+0x28,r1=1`. The pinned 8-byte target is `STR r1,[r0,#0x14]; BX LR`, so it writes axis-1 start=1 and returns through the original LR. This target is an interior entry in the neighboring image range, not a separately listed function row.

The direct cursor writes are `+0x50` (word), `+0x62` (byte), `+0x5C/+0x5E` (halfwords), and `+0x14` (word); helper effects add the two axis records. No global access is visible in this body.

## Direct call map and unresolved boundaries

Calls occur in this order on an active path: divider `0x002C615C`; axis-0 initializer `0x00296F18`; axis-0 base IDs `0x00296EF8`; optional axis-0 extended IDs `0x003170A0`; axis-1 initializer `0x00296F18`; axis-1 base IDs `0x00296EF8`; optional axis-1 extended IDs `0x003170A0`; then the non-linking tail branch to `0x002FC20C`. Axis-0 and axis-1 initializer sites are mutually exclusive pairs as specified above. The three record helpers have direct, narrow byte/word contracts in their function records/source. `0x002C615C` has a separately documented quotient/remainder contract; this task did not execute any helper.

Pinned caller/source references also show use outside H2: `0x002338C4`, `0x001E034C`, `0x00262F6C`, `0x0028EC90`, `0x002A02C8`, and status/UI routines at `0x00215990`, `0x00215A68`, and `0x002F6620`. These callers use different setup values. An aligned ARM BL-word scan produces additional candidate references, but embedded data and indirect calls prevent treating that scan as a complete caller census. No other caller is used to infer the H2 contract here.

The H2 path with `(cursor,3,3,1,0,1)` computes rows=3, takes the zero-wrap axis-0 route, and makes exactly these calls to the record initializer: `0x0029FBC4(cursor,3,3)` and `0x0029FC44(cursor+0x28,1,1)`. With repeat=1 the axis ID bytes at `+4..+11` are `(6,5,32,32,15,14,32,32)` and `(3,4,32,32,12,13,32,32)`. The final ten words for each record are:

- axis 0: `(6,0x20200506,0x20200E0F,0,3,1,3,3,0,0)`;
- axis 1: `(6,0x20200403,0x20200D0C,0,1,1,1,1,0,0)`.

The word at `+0x14` is 2 immediately after `0x00296F18`; it is overwritten to 1 on both axes by this wrapper/finalizer. Thus the pinned final H2 cursor has both starts equal to 1. A prior `0x001FF3C4` note that calls axis0 start=2 the final setup state conflates the intermediate helper output with the completed caller path; this report does not edit that shared contract.

## Bounded C++ scope and conversion feasibility

A readable orchestration-only C++ conversion appears feasible in the 452-byte span if it preserves these original dependencies and exact call order, uses explicit 32-bit stack/callback argument handling, retains the no-clear disabled path, and emits the final stores/tail behavior. The existing body is 113 ARM words and contains many alignment NOPs, but that alone does not prove a compiled C++ body will fit. No compiler measurement or relocation/final-address support test was assigned or performed. A later candidate must measure slot fit and resolved call targets, prove ARM interworking, and run a caller differential with complete write/call traces before conversion or promotion is accepted.

The bounded domain is an aligned, writable cursor record with valid storage for both 0x28-byte axes plus header fields, and calls to the pinned helpers. Zero/negative columns, malformed totals/visible values, overlapping records, invalid pointers, concurrent observation, MMIO, helper faults, task/input timing, runtime title reachability, and full H2/audio behavior remain outside this static contract. Keep the helper calls as dependencies until each is independently validated; do not infer input meanings, audio behavior, or whole-TitleConfig equivalence.

## Provenance

- Pinned image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Original 452-byte slice SHA-256: `775855685fc946151107ff9a787cce85eee1ef29b839e558628ddcc3429e58b9`.
- Naked source mirror SHA-256: `3ebf6bb17e01ac9eb9b678f85307e7d4fcf09c83417e752b09b1dfa475dfbfe3`.
- All hashes in the prepared run001 `input_sha256` object recomputed without mismatch.

Read-only checks: decoded the pinned 452-byte ARM body and the `0x002F4D90` caller window with Capstone; scanned aligned ARM `BL` words for the principal callees; searched checked-in source references for setup callers; and recomputed packet input hashes. No source, runner, ledger, board, build cache, or emulator state was changed.
