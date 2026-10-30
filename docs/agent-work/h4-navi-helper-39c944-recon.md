# Navi helper `0x0039C944` static reconstruction

## Scope and provenance

This is a read-only static reconstruction of the pinned ARM image (`code.bin` SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`). The function ledger assigns `0x0039C944` a 576-byte span and ARM mode. The entry is word aligned and has no Thumb interworking bit. The executable body begins at `0x0039C944`; the main reachable code ends at `0x0039CB60`, followed by literal words at `0x0039CB64..0x0039CB6C` and code-looking words at `0x0039CB70..0x0039CB83` with no branch or BL reference found from the entry body. I do not attribute that trailing sequence to the helper's reachable behavior.

## ABI and control flow

The prologue saves `r4-r7,lr`, saves VFP `d8`, and allocates `0x14` stack bytes. `r4` retains the input object pointer; `r5` is `object+0x5A8D` (a byte marker); `r6` is `object+0x162`; `r7=1`. The code uses stack locals for two words returned by a query and two coordinates. The epilogue restores stack, `d8`, and `r4-r7`, then returns with `pop {...,pc}`. The function has no explicit canonical return assignment: `r0` is path dependent and can retain a helper result or an intermediate value. No general return-value contract is established.

At entry it reads `object+0x10` and tests mask `0x20000`.

- If set, it calls `0x002C01B0` with output pointers in the local stack area. A zero result goes to the common flag/position update path. For a nonzero result it reads byte `[0x0049F91C+0x18]`; zero selects the coordinate/repeat path at `0x0039CA9C`, while nonzero selects the common update path.
- If the entry bit is clear, it skips that query and enters at `0x0039C9E8`.
- The common update path clears bits `0x30000` in `object+0x10`. It reads signed byte `object+0x54`; if greater than 2 it zeros float fields `+0x3C` and `+0x40`, otherwise it sets them to the differences `(+0x44 - +0x4C)` and `(+0x48 - +0x50)`. If bit `0x20000` remains set, it exits.
- Otherwise it compares the absolute values at `+0x3C` and `+0x40` against float `0.5`. If both are at most `0.5`, it zeros both fields and exits. If either exceeds that threshold, it multiplies both by the float at `0x0044CDC8`, calls `0x0039FA68(object+0x162)`, reads a two-word pair through `0x00231F58(object+0x162)`, adds each scaled delta divided by the returned float to that pair, and passes the pair to `0x00231B38(object+0x162, pair)`. It then writes byte `1` to `object+0x5A8D` and exits. The gate byte at `0x0049F91C+0x18` is separate from the multiplier float.
- The coordinate/repeat path calls `0x0039FA68(object+0x162)`. It uses the two local words from `0x002C01B0`, fields `+0x2C/+0x30`, and fields `+0x34/+0x38` to calculate a coordinate pair, then calls `0x00231B38(object+0x162, pair)`. It compares the local integer coordinates converted to float against `object+0x44` and `object+0x48`. If both match, it increments signed byte `object+0x54` up to 99. If either differs, it resets that byte to zero, copies the prior coordinates `+0x44/+0x48` into `+0x4C/+0x50`, and stores the new coordinates at `+0x44/+0x48`. It writes byte `1` to `object+0x5A8D` and loops to the common bit/position path.

The observable direct object effects are thus conditional updates to word `+0x10`, floats `+0x3C/+0x40`, `+0x44/+0x48`, `+0x4C/+0x50`, signed byte `+0x54`, and byte `+0x5A8D`. The prologue and body also read object fields `+0x10`, `+0x2C..+0x50`, and `+0x54`. No null check or object-size check is present; callers must supply a readable/writable object spanning these offsets on the selected path.

## Calls and transitive effects

Direct callees are `0x002C01B0`, `0x0039FA68`, `0x00231F58`, and `0x00231B38`. The first supplies local coordinate words and a status result; the `0x0039FA68` result is consumed as a float divisor; `0x00231F58` supplies a two-word pair; `0x00231B38` receives a coordinate pair. Their contracts, pointer validity, and complete side effects are not proven here. In particular, host state changes through `0x00231B38` or reads through `0x00231F58` are transitive dependencies, not direct writes to the object. A candidate implementation needs these helper contracts and their numeric edge behavior (including the divisor) before these paths can be safely replaced.

## Caller and observed invocation

A pinned-image aligned BL scan finds one direct caller: `0x00399DA8` in callback `0x00399D60`. The callback first requires nonzero results from `0x002C0BA8(0x400)` and `0x002931CC(0x76)`, then requires unsigned `LDRB [object+0x0C] != 0`; it passes the object pointer in `r0` to this helper. The callback's saved `object+0x10` bit `0x1000` is tested only after the helper call.

The independently reviewed run-004 trace records the helper call returning to `0x00399DAC` with `r0=0` in that one sampled invocation. The subsequent observed callback path proceeds through `0x00399DB8`, then `0x00399DCC`, and returns to `0x001A95E8` with `r0=0`. This is one invocation at the captured checkpoint only; neither the helper nor callback has a general fixed-zero return contract. The trace does not establish input semantics, movement, interaction, ownership, complete object mutations, or transitive host effects.

## Remaining blocker

Before implementing a semantic replacement, independently reconstruct or bound the four direct callees, especially the state/pointer contracts of `0x00231F58` and `0x00231B38`, the coordinate/status contract of `0x002C01B0`, and the valid range/nonzero guarantees of the `0x0039FA68` divisor. The accepted callback sample is insufficient to resolve those branches or validate the direct write set dynamically. No build, test, emulator, source-save, or guest-memory operation was performed.
