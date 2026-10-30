# H1 type-1 callback candidate: `0x00151404`

## Result

Implemented the callback as experimental readable C++ in
`experiments/semantic_equivalence/h1_type1_callback_candidate.cpp`. The
callback preserves calls to the original float helpers at `0x002A337C` and
`0x0014D608`. A fresh isolated runner compiled the candidate and compared it
with the pinned original ARM body and those original helper bodies.

The candidate matches all ten completing directed cases across return `s0`,
FPSCR, helper ABI arguments, callee-saved registers, SP, and data-memory
effects. Cases cover zero interval, equal/below/inside/at/above sample,
positive/negative interval, a rounding boundary, and quiet NaN. A further
positive-infinity case reaches the original exceptional `BLX 0x002A464E`; both
executions fault at PC `0x002A4656` when that original path writes into the
read-only mapped text page. It is therefore a recorded domain limit and not a
completed-return equivalence case. The candidate fails two deliberate
mutations: replacing ARM unordered `BLE` behavior with C++ ordered `<=`, and
skipping the original integral-float helper.

The original caller evidence gives `r0` as a context pointer and the three
float inputs in `s0-s2`; the observed caller consumes returned `s0`. `r0` is
caller-saved and overwritten by that caller after return. Registration evidence
does not prove live selection of callback `0x00151404`. No caller integration,
runtime, visible UI, or emulator evidence is claimed.

## Validation

Commands (both exit 0):

1. `python -m unittest tests.test_h1_type1_callback_experiment -v`
2. `python tools/h1_type1_callback_experiment.py --output build/agent-work/H1-semantic/h1-type1-callback-candidate/sleep-20261025-type1-callback`

The runner pins `code.bin` SHA-256
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`, checks
the original callback boundary and disassembles all callback words through
`0x00151464` (literal/data words start at `0x00151468`). Candidate symbols have
zero relocations; validation checks their decoded return boundaries, local
branches, and every PC-relative `ldr`/`vldr` against the bounded literal tail.
The run object and machine-readable per-case report live in the task output
directory; their current hashes are in `handoff.json`.

## Evidence classification and next step

- Static: pinned callback instruction window, registration/caller evidence,
  and direct helper disassembly.
- Synthetic: isolated Unicorn comparison using generated values and the pinned
  original ARM helpers. No runtime state sampling.
- Runtime: not run; callback runtime selection unproven.

Ready for independent review of the function contract, helper ABI, candidate
source/object, exact branch/zero behavior, directed case quality, fault
accounting, and evidence limitations. Promotion/integration remains a separate
coordinator decision after review and caller/runtime evidence.
