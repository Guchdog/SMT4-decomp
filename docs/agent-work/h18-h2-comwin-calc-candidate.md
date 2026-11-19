# H18 experimental reconstruction: `ComWin_Calc` entry `0x0011b094`

## Recovered behavior

The callback loads the work pointer through global word `0x0043e0f8`, reads the 32-bit state at `work+8`, and dispatches states 0 through 4 through an in-body jump table. States 0, 3, and all values greater than 4 go directly to the common counter increment. State 1 calls widget calc `0x002bf9f0(work+0x3c)`; if the result is nonzero, it writes state 2 and counter 0 before the common increment. State 2 calls `0x002bf9f0(work+0xc8)` and ignores its return. State 4 calls `0x002bf9f0(work+0x3c)`; a nonzero result writes state 0. Every path increments the current 32-bit `work+0x0c` by one, with unsigned wraparound, then returns `r0=0`.

The callable ABI exercised is a callback entered with a synthetic `LR`; its incoming `r0` is ignored. `r4-r6` and SP are preserved by both original and candidate, and the callback returns zero. The helper ABI is one work pointer in `r0`, with its 32-bit result in `r0`. Its body is intercepted by the runner. Explicit modeled helper writes to state/counter fields show the original's read/write order: state dispatch uses the pre-call state, state 1 with a nonzero result overwrites helper writes, state 1 with zero leaves helper state mutation intact, and counter increment reads the post-call/current counter except when state 1's nonzero path first resets it.

## Offline evidence

`experiments/semantic_equivalence/h18_h2_comwin_calc.cpp` holds an experimental candidate only. The runner compiles it in a private output directory, injects it at `0x0011b094` in a private Unicorn image, intercepts calls to `0x002bf9f0`, and compares return, SP, callee-saved registers, work bytes, and helper argument/result traces against the pinned original. It covers all states 0–5 and `0xffffffff`, three helper results, counter wrap, and explicit helper side effects. All 27 fixtures passed. A compiled negative control that inverts the state-1 helper gate is detected.

The in-span jump table at `0x0011b0b4..0x0011b0c7` resolves to `0x11b110`, `0x11b0c8`, `0x11b0ec`, `0x11b110`, and `0x11b100`; the literal at `0x11b124` is `0x0043e0f8`. These checks bound the switch table and global pointer load.

## Registration, overlap and limits

The static reconstruction identifies `ComWin_Init` registering the callback under `ComWin Calc`. The function entry `0x0011b094` is an interior 148-byte subentry inside the 792-byte ledger/source span beginning at `0x0011ae10` (`InfoWin_DrawUp`). It has no independent CSV ledger row. This work leaves the source placeholder, compound span, ledger and production image untouched; the experiment applies the candidate only in private emulation memory.

The widget helper is a deterministic trace stub with configured return values and optional explicit work mutations. No `0x002bf9f0` internal behavior, task scheduler semantics, live ComWin object, registration sequence, natural callback invocation or runtime UI behavior is established. The direct callback tests are composition tests for the entry ABI, not proof of a natural caller or H2 input-query relationship.
