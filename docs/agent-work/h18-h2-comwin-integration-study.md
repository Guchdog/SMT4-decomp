# H18 ComWin_Calc private integration study

## Staging and boundaries

The experimental `h18_h2_comwin_calc_candidate` compiles to 144 ARM bytes, has no unresolved relocations, and fits the 148-byte callback subentry at final VMA `0x0011b094`. The runner pads the final slot to 148 bytes, builds an IPS from the original pinned image, replays it, and compares the staged image byte-for-byte against the expected result. The patch changed 128 file bytes; every changed byte lies within the callback subentry. The enclosing `InfoWin_DrawUp` span remains `[0x0011ae10, 0x0011b128)`; bytes before and after the subentry were checked unchanged.

The callback entry and widget target `0x002bf9f0` are even addresses, indicating ARM state. The candidate contains three register `BLX` call sites; the final-address run reaches the widget hook with the expected `work+0x3c` argument in state 1. This validates its ARM-state call target with the emitted interworking instruction and runtime trace. Candidate code and IPS exist only under the private run output.

## Registration/caller composition

The runner starts the pinned original `ComWin_Init` at `0x0010a748`. It executes through original argument setup and the actual `BL 0x002c5978` call boundary for `AsdTask_CreateCalc`. At that boundary it captures the string `ComWin Calc`, task tag `1`, and callback address `0x0011b094` from the original stack argument. The wrapper itself is intercepted and returns a synthetic task handle. Allocation (`0x002c4b84`) and zeroing (`0x002c4b30`) are modeled to provide and clear one private work block.

Using the captured callback pointer, the runner invokes the callback once with post-init state (state 0/counter 0) and once with an explicit state-1 fixture. Both original and staged images register the same pointer and produce identical callback snapshots. The post-init callback returns 0 and increments the counter to 1; the state-1 run with widget result 1 moves state to 2, sets the counter to 1, returns 0, and calls widget calc with `work+0x3c`.

## Limits

This composes the actual `ComWin_Init` caller instructions up to the `AsdTask_CreateCalc` wrapper boundary, but does not execute the wrapper's internal task-manager registration or scheduler. The allocation and zero helpers are controlled seams. Callback invocation is explicit through the captured registration pointer; it is not a naturally scheduled UI cycle. The widget helper is a configured stub, not its real implementation. The candidate remains an experimental overlap within a compound source/ledger span; this task changes no source placeholder, production span, ledger, canonical build cache, installed IPS or emulator state.
