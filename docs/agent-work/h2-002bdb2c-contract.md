# Static contract: TitleConfig sprite setup `0x002BDB2C`

Status: recovered from pinned US v0.1.0 ARM and the `titleConfig_func_002f4ca0` call sequence. No candidate, compiler, build, differential, or emulator run was performed.

## Identity and proven caller

`0x002BDB2C..0x002BDBC4` is the 152-byte ARM span in `extracted/exefs/code.bin` (image SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; span SHA-256 `250f01439d7532fe72009449a21f82c0b808ec72984da4a004fbe87f9d8456e4`). Its checked-in source mirror is `src/engine/leaf_batch30_c.cpp`, SHA-256 `fe96c8a458daae0b24b38aeb6e58849edbcf65ed711c1e02a6c9d1ff0ae39e08`.

The pinned caller is `titleConfig_func_002f4ca0` at `0x002F4CA0`. At `0x002F4D6C..0x002F4D88` it sets stack argument `[sp]=0xC9`, loads `s0=1.0f`, sets `r3=work+0x3C`, `r2=0`, `r1=0x2F`, `r0=work+0x5C`, and BLs this function. The `TitleConfigWork` layout in `include/camp/title_flow.h` identifies these as the 0x8C-byte sprite at `+0x5C` and its 0x20-byte group at `+0x3C`.

Immediately before setup, the caller initializes the group with `0x002C3344` and binds it through `0x002C32F8`: table word `0x00407EC6`, count `0x18`, and zero values for the remaining descriptor words. The binder's own ABI consumes the first three stack words as halfwords and later stack words as raw float payloads; the caller zeros all seven stack words. Thus the descriptor contains the table word at `group+0x0C`, zero at `+0x10`, and zero payload at `+0x14..+0x1C`. The setup body copies those five words to sprite offsets `+0x4C`, `+0x58`, `+0x64`, `+0x70`, and `+0x78`. This establishes the caller-specific memory values, not the contents/meaning of the table or the rendered result.

## Mixed ABI and machine-level return

The entry consumes six logical arguments split across integer registers, the stack, and VFP:

| Location | Meaning | TitleConfig value |
| --- | --- | --- |
| `r0` | writable sprite node | `work+0x5C` |
| `r1` | type/resource-group selector | `0x2F` |
| `r2` | sprite/resource index | `0` |
| `r3` | `UiSpriteGroup*` | `work+0x3C` |
| entry `[sp]` | 16-bit panel/selector field | `0xC9` |
| `s0` | scale float | `1.0f` (`0x3F800000`) |

The prologue preserves `r4-r8`, `r9` (`sb`), `r10` (`sl`), LR, and `d8`; SP is restored by the epilogue. It copies `s0` into callee-preserved `s16`/`d8` before calling `0x002C4B30` and restores `d8` on return. The call to `0x002C4B30` is `AsdMem_Zero(sprite,0x8C)`; the helper increments `r0` as it clears, and this function does not overwrite `r0` afterward. Consequently, the current machine-level `r0` on return is the end pointer `sprite+0x8C`. The known TitleConfig caller ignores it. Preserve that raw result if the replacement's contract includes caller-saved result observability; a `void` source declaration alone does not describe the exact post-call register value.

No explicit stack frame is allocated beyond saved registers. The single consumed stack word is read from `[sp,#0x28]` after saving 32 bytes of GPRs and 8 bytes for `d8`, i.e. the caller's original `[sp]`. `s0` is a true VFP argument; it is not a float reinterpreted from the integer stack word.

## Reads, ordered calls, and writes

The only direct helper call is `0x002C4B30(sprite,0x8C)`, before any field writes. It clears exactly the 0x8C-byte sprite node. The remainder of the body reads the input arguments and five group words, then writes:

| Sprite offset | Write |
| --- | --- |
| `+0x00` | `r1` type/resource-group selector |
| `+0x04` | `r2` index |
| `+0x08` | `0xFFFFFFFF` |
| `+0x20` | incoming `s0` scale |
| `+0x24`, `+0x28`, `+0x2C` | `1.0f` each |
| `+0x38` | low 16 bits of entry `[sp]` |
| `+0x48` | `r3` group pointer |
| `+0x4C`, `+0x58`, `+0x64`, `+0x70`, `+0x78` | words loaded from group offsets `+0x0C`, `+0x10`, `+0x14`, `+0x18`, `+0x1C` respectively |
| `+0x86..+0x8A` | five bytes set to `1` |

All remaining node bytes stay zero from the helper clear. The function does not dereference a resource table, allocate/load a resource, call a renderer, or mutate the group. Its direct group reads assume `r3` is a readable pointer with at least 0x20 bytes; its node writes assume `r0` points to a writable 0x8C-byte region. There are no null/bounds checks.

## Resource/group interpretation and source declaration caveat

For the TitleConfig caller, the helper receives selector `0x2F`, index `0`, group pointer `work+0x3C`, panel value `0xC9`, and unit scale. The group is initialized/bound to the raw table word `0x00407EC6` and count `0x18`; the function merely copies selected descriptor words into the sprite. The table extent, resource/group lookup rules, panel semantics, allocation/lifetime, renderer interpretation, and visible output remain external contracts. Do not infer 24 visible assets or that setup alone draws a sprite from the descriptor count.

There is a checked-in declaration inconsistency: `src/ui/window.cpp` has a legacy seven-argument `UiAnimSprite_SetupEx(sprite,type,id,a3,group,flag,scale)` declaration and several callers using that shape. This ARM body unambiguously consumes the group in `r3` and the panel value at entry `[sp]`; a separate integer `a3` before the group is not part of this ABI. The corrected SearchWin local alias in that file uses the six-argument shape `sprite,type,id,group,panel,scale`, matching the pinned TitleConfig call. The task only establishes the TitleConfig caller; other call sites should be checked against their pinned call instructions before relying on their C++ declaration.

## Conversion recommendation and validation scope

A bounded readable C++ replacement looks feasible: retain the exact `AsdMem_Zero` dependency, assign the explicitly listed fields in the same externally observable order where required, and express the true mixed ABI with `r3=group`, one integer stack argument, and `s0=scale`. Keep resource interpretation outside the candidate. The 152-byte slot is not a reason by itself to choose opaque assembly; no compilation or fit proof was made here. Because the raw machine result is `sprite+0x8C` even though TitleConfig ignores it, decide explicitly whether the replacement must retain that result before implementation.

The focused differential should compare the full 0x8C output against the original with poisoned initial bytes, group descriptors with both TitleConfig values and varied nonzero fields, panel/index/selector boundaries, scales including `+0`, negative/finite values and non-finite bit patterns if supported, and a negative control for group argument placement. Assert the 0x8C clear and all field offsets, preserve `r4-r10`, SP and `d8-d15`, inspect raw `r0` if within the chosen contract, and compose the exact `titleConfig_func_002f4ca0` call tuple. Keep table contents, resource loading/rendering, and scheduler effects as explicit untested dependencies.

## Provenance and checks

- Reference image SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Original 152-byte span SHA-256: `250f01439d7532fe72009449a21f82c0b808ec72984da4a004fbe87f9d8456e4`.
- Target source SHA-256: `fe96c8a458daae0b24b38aeb6e58849edbcf65ed711c1e02a6c9d1ff0ae39e08`.
- Every run001 declared input hash recomputed successfully.
- Read-only checks: `python -B tools/split_asm.py --addr 0x002bdb2c --limit 1`; `python -B tools/split_asm.py --addr 0x002f4ca0 --limit 1`; pinned source/header/layout inspection; packet SHA-256 verification.

No source, ledger, README, milestone, board, build cache, or emulator state was changed.
