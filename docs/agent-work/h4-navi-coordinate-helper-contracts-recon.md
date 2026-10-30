# Navi coordinate-pair helper contracts

## Scope and source identity

Static inspection against pinned ARM image `extracted/exefs/code.bin`, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The ledger assigns `0x00231F58` a 20-byte ARM span and `0x00231B38` a 28-byte ARM span. Both entries are word-aligned ARM code. I checked the full function spans, their Navi caller windows, and an aligned ARM BL scan in `[0x00100000,0x003FE624)`. This is a bounded direct-call scan; indirect/Thumb references and accesses outside it remain unproven.

## `0x00231F58`: get address of host pair

Instructions:

```text
00231F58  ldr r0, [pc, #8]       ; literal at 0x00231F68 = 0x0044CDF0
00231F5C  ldr r0, [r0]          ; host = *(u32*)0x0044CDF0
00231F60  add r0, r0, #0x38
00231F64  bx  lr
```

The function ignores its incoming `r0` and returns the address `host+0x38` in `r0`. It does not load either pair word itself. The target pair comprises two consecutive 32-bit words at host `+0x38` and `+0x3C`. No stack, store, status calculation, null/range check, or other register write is present. At the instruction level only `r0` is changed; no flag-setting form is used. If the slot contains null, this function still computes and returns address `0x38`; a later caller dereference can fault. Slot readability and pointer validity are caller/environment dependencies.

## `0x00231B38`: copy two words to host pair

Instructions:

```text
00231B38  ldr r0, [pc, #0x10]   ; literal at 0x00231B50 = 0x0044CDF0
00231B3C  ldm r1, {r1, r2}      ; load source words before host dereference
00231B40  ldr r0, [r0]          ; host = *(u32*)0x0044CDF0
00231B44  str r1, [r0, #0x38]
00231B48  str r2, [r0, #0x3C]
00231B4C  bx  lr
```

Incoming `r0` is ignored. `r1` must address two readable 32-bit source words; the first is loaded into `r1`, the second into `r2`, before the global host pointer is loaded. The routine writes those words, in order, to host `+0x38` and `+0x3C`. It returns in `r0` the loaded host pointer as a residual value, not a success flag. `r0-r2` are changed; other general registers are untouched. There is no stack use, VFP work, status/null/range/alignment check, lock, or flag-setting instruction. The two stores are separate, so the body does not provide an atomic pair update. Invalid source/global/host pointers can fault; exact fault behavior is not characterized here.

The literal/global slot is reread on every setter call. A caller that gets a pair address, computes a result, and later calls the setter is not guaranteed by these bodies to use the same host allocation if the global slot can change between calls. No synchronization or host lifetime contract is established.

## Navi callsite data flow

In `0x0039C944` the local `r6` is `object+0x162`. The calls pass this as incoming `r0`, but neither helper uses that argument as the host pointer:

- At `0x0039CA44`, `0x00231F58` returns `host+0x38`. The caller loads word 0 to `r1` and word 1 to `r0`, then saves both to stack locals at `[sp]` and `[sp+4]`. Separately, the earlier `0x0039FA68` call returned the divisor in VFP `s0`, saved as `s16`. The caller divides the scaled object deltas `+0x3C/+0x40` by `s16`, adds each result to one loaded host-pair word, stores the calculated words to `[sp]`/`[sp+4]`, and calls `0x00231B38` at `0x0039CA88` with `r1=sp`. Setter copies the calculated pair to current host `+0x38/+0x3C`. The accessor/divisor result, getter's original pair, callback-object fields, and setter's stored pair are distinct data-flow values.
- On the separate coordinate branch, `0x0039FA68` is called at `0x0039CAA0`; its `s0` result divides integer query outputs converted to float after subtracting callback-object fields `+0x2C/+0x30`. Those results are offset by callback-object fields `+0x34/+0x38`, placed at `[sp+8]` and `[sp+0xC]`, and passed as `r1=sp+8` to setter at `0x0039CAEC`. This branch does not call the getter at `0x00231F58`. The pair values stored in global host state are the computed coordinate pair; they are not the accessor's host `+0x34` divisor and are not necessarily the object fields at `+0x34/+0x38` themselves.
- Other inspected Navi-family use includes getter at `0x0039B6BC` followed by copying its pair into object-relative `+0x34/+0x38`, and setter at `0x0039B748` after a pair is built in stack locals. `0x0039D83C` also calls the getter and copies its returned words into object-relative `+0x34/+0x38`. These sites use the same absolute global slot in the helpers; they do not independently establish gameplay meaning or object ownership.

The bounded aligned BL scan found direct getter callsites at `0x00399B68`, `0x00399F6C`, `0x0039B1E0`, `0x0039B6BC`, `0x0039B804`, `0x0039BA28`, `0x0039BAB0`, `0x0039BB34`, `0x0039CA44`, `0x0039D010`, `0x0039D83C`, `0x0039E7A0`, and `0x0039EDA4`; direct setter callsites at `0x0039B028`, `0x0039B748`, `0x0039B840`, `0x0039BA60`, `0x0039BAE8`, `0x0039BB5C`, `0x0039CA88`, and `0x0039CAEC`. Only the `0x0039C944` paths above were data-flow traced in detail for this task; other direct references are xref evidence, not individually recovered caller contracts.

## Bounded contract and unresolved points

For a valid global slot and host pointer, `0x00231F58` returns a pointer to two host words without reading the pair; `0x00231B38` reads a two-word source pair and copies it into host `+0x38/+0x3C`. Neither function says whether the words are coordinates, velocity, input, or any game-specific state. The naming “coordinate” here describes only the caller's observed float arithmetic and pair usage, not a proven semantic type.

Open items include pointer lifetime/ownership for `0x0044CDF0`, whether any concurrent writer can retarget it between calls, alignment/fault behavior, atomicity requirements for readers of the pair, and the full contracts of other callers. The separate divisor at global-host `+0x34` comes from `0x0039FA68`; it is not the pair these helpers expose. No C++ implementation, build, emulator, private profile/save access, or guest-memory operation was performed.
