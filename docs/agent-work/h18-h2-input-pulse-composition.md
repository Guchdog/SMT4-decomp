# H2 input pulse composition

## Result

An offline Unicorn composition exercised the pinned `code.bin` and a staged replacement chain. The replacement used compiled C++ for the `0x0011c5ec` reader and `0x001078d8` refresher, plus the typed `0x002c1830` dispatcher and `0x002bffbc` mode-1 helper. The reader's external ring producer at `0x0012a758` remained an explicitly controlled seam. Each event supplied one synthetic ring record; it did not emulate physical controller input or the game's real ring producer.

The dispatcher candidate calls the compiled mode-1 candidate from scratch address `0x00800000`. That helper compiles to 68 bytes, while its original function span is 60 bytes. The runner therefore avoids patching over adjacent original code and maps the candidate into an independent page. The mode-1 helper candidate's behavior is exercised within the composed query call.

The wrong-counter negative control also runs from that scratch page. The runner saves the exact good and mutant helper bodies as `mode1-helper.bin` and `wrong-counter-mutant-helper.bin`, with SHA-256 values and mapping/reproduction instructions in `scratch-helper-manifest.json`. It does not label a duplicate candidate image or IPS as a mutant artifact; the code image and IPS remain the same for the good and mutant runs, while only the scratch helper bytes differ.

## Evidence

For release, press, held, release, press-again, both original and candidate produced counter/query pairs `0/0, 1/1, 2/0, 0/0, 1/1`; all five projected snapshots matched. The traces confirm one ring call per refresh, normal stop/stack behavior, preserved callee-saved registers, dispatcher arguments `(0,1)`, and no query-side external writes.

Additional cases matched original and candidate:

- Ring count zero leaves availability false and retains the prior counter. A prior counter of one therefore yields a stale query pulse until an available release refresh clears it.
- Query flag bit 0 suppresses mode-1 primary query even while the counter stays one; clearing the flag permits the stale pulse again.
- A nonzero row gate resets the counter and query result to zero.
- A wrong-counter mutant is detected: good press query is one, mutant query is zero.

The logical input under test is the low bit of the synthetic ring record delivered through the reader seam. Results establish this offline composition for those fixed cases, not a binding between a physical button and that bit, nor a runtime/game-wide equivalence claim.

## Reproduction

```powershell
python -m py_compile tools/h18_h2_input_pulse_composition.py
python -m unittest tests.test_h18_h2_input_pulse_composition -v
python tools/h18_h2_input_pulse_composition.py --output-dir build/agent-work/batch-h18-001/h18-h2-input-pulse-composition/run-002/checks/verified-001
```

The final report and staged images are under `build/agent-work/batch-h18-001/h18-h2-input-pulse-composition/run-002/checks/verified-001/`. Original `code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; candidate image SHA-256 is `658116cc69fd43318ed233e6d367f393aab49b73778f4f098c25157a33778157`. This was offline validation only; no emulator or canonical full build was run.

## Next step

Integrate/review this chain against the natural runtime input producer and caller cadence. Preserve the distinction between a one-refresh logical pulse and physical input semantics; capture a real producer sample before promoting a physical-input claim.
