# H2 production Calc + Draw placement

## Result

An offline production-derived IPS now combines `TitleConfig_Calc` with the
production `TitleConfig_Draw` body and its outlined cache helper. The image is
reproducible from the pinned US `code.bin`, the production Calc TU object, and
the frozen production Draw TU object. The combined image SHA-256 is
`eaac1ebd0875436210b49e5c0874ab93d7087a47b52847b85bc8f3f59b003186`; the IPS
SHA-256 is `447b635cf0b0a58fcfc0fc2f4a2bc5ce852a3d7f34775cf8b29dc8262630b185`.

This is offline final-address differential evidence, not Azahar/runtime
acceptance. After independent review, the Draw ledger row is classified
`non_matching` to reflect the production replacement bytes.

## Exact placements

| Piece | VMA / range | Bytes | Resolution |
|---|---|---:|---|
| Calc entry | `0x001EA928` | 4 | ARM branch to `0x003FE624` |
| Calc body | `[0x003FE624,0x003FEE54)` | 2,096 | Four local `R_ARM_ABS32` references rebased to the cave body |
| Draw main + trailing pool | `[0x002CAFD0,0x002CB588)` | 1,464 | In-place; seven `R_ARM_CALL` sites branch to helper; one `R_ARM_ABS32` targets the copied `%s\0` |
| Draw cache helper | `0x003FEE54` | 124 | ARM BL target from the seven call sites |
| Draw format literal | `0x003FEED0` | 3 | Exact bytes `%s\0` |

The helper/string payload rounds to 128 bytes in the 428-byte cave tail, leaving
300 bytes. The patcher checks the original `.text` layout and zero cave, object
and source hashes, exact symbol sizes/relocation map, ELF section/addend
resolution, ARM BL encoding and range, the full `.text` suffix branch graph,
IPS round-trip, and that bytes outside the authorized records remain unchanged.

The Draw object has 1,424 bytes of code followed by a 40-byte literal pool. Its
last instruction is `pop {..., pc}` at `0x002CB55C`, before the literal pool
and the retained original suffix beginning at `0x002CB588`. The static suffix
scan found nine branches targeting `[0x002CB588,0x002CB75C)`: two originate in
the overwritten main (`0x002CB0AC→0x002CB74C` and
`0x002CB580→0x002CB6D4`), and seven are internal to the retained suffix. No
external direct branch or aligned absolute pointer enters that suffix. The
replacement returns before the suffix; the old `%s` address is only referenced
by an ADR inside the replaced range.

## Differential and caller evidence

Final-address runs used the same combined image:

- Draw: 46/46 directed cases passed, comparing work/config/cache bytes, ordered
  service traces, return/fault state, and callee-saved registers/SP/d8-d15. The
  format-string pointer itself is expected to move; formatted text and its
  arguments were compared. A helper-call-target-plus-four mutation was
  detected. The earlier wrong-TBB-stride negative control remains recorded in
  the isolated Draw candidate report.
- Calc: 16/16 persistent sequences and 54/54 ticks passed for seeds 7 and
  20261024. The wrong logical-map control was detected.
- Initializer caller composition: 3/3 State 9/10 cases passed using the same
  combined image, with the wrong Calc callback registration control detected.
  The initializer itself was injected by the caller harness; this does not
  schedule either callback or prove initializer production integration.
- H2 offline regression: 67 unit tests passed, including the local-socket RSP
  probe tests. No Azahar process, debugger connection, profile, or host input
  was used.

## ABI and remaining limits

The task factory helper in `src/engine/asd_render_ui.cpp` exposes callback
addresses as `void (*)(void*)`. The pinned Draw callback's normal machine return
has `r0=0`, which the replacement also produces. The task callback ABI does not
consume a C return value; the typed `void TitleConfig_Draw(void*)` declaration
is separate from the ledger-named global C entry `ui_func_002cafd0`. No shared
header change is needed for this patch.

Renderer, cursor, layout, TBB, format/font, touch, and indirect callback
internals remain matched HLE boundaries. The caller harness checks callback
registration but does not schedule Draw/Calc. There is no visible UI, real
input, persisted setting, cross-session persistence, or Azahar runtime
comparison. The current evidence does not close H2.

## Reproduction

Patcher and manifest:

```powershell
python tools/h2_combined_code_patch.py `
  --calc-object build/agent-work/H2-semantic/h2-calc-production-integration/run-001/checks/final-seed-7-20261026/leaf_batch46_b.o `
  --draw-object build/agent-work/H2-semantic/h2-draw-cache-split-probe/run-001/checks/production-tu/engine/leaf_batch43_a.o `
  --output build/agent-work/H2-semantic/h2-combined-code-placement/run-010
```

Offline final-address and caller runs are recorded under
`build/agent-work/H2-semantic/h2-combined-code-placement/run-010/`.
