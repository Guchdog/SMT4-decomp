# Independent review: H1 navigation adapter matrix

## Verdict

**The corrected bounded caller-window differential is supported; evidence is
partial.** I verified the matrix report and runner without compiling or running
the test. The original machine is left on the pinned image, while only the
candidate machine has the inline-entry branch patched to the compiled shim.
The report contains the complete 256-element Cartesian product, both false
readiness gates, no first mismatch, and the intended signed-remainder mutation
counterexample. I found no discrepancy in the corrected run's bounded setup or
reported projection.

## Important correction to the earlier experiment

tools/h1_navigation_adapter_experiment.py has a defect in AdapterMachine.run:
it rewrites the instruction at CALLBACK_START to branch to the injected
adapter unconditionally, including when its mode string is "original".
Therefore the earlier five-case differential and its three negative-control
comparisons did not compare original inline ARM against the candidate. The
earlier review missed this image patch and its differential verdict is
withdrawn. Its pinned-image disassembly, control-flow, live-register, and ABI
analysis remains useful static evidence. A dated correction was added to that
review file; its old differential report must not be cited as proof of
original-versus-candidate equivalence.

The new matrix runner uses two separate machines. Its original_machine starts
at 0x001E9D08 without writing to the image. Its adapter_machine alone is passed
to patch_inline_window, which changes the first four bytes at that one entry to
branch to the injected shim. The matrix then executes each machine from the
same entry and matching synthetic state. The negative-control machine is
separately patched to run the mutant candidate. This fixes the key evidence
flaw in the older harness.

## Identity, cases, and controls

- Pinned code image SHA-256: 1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558.
- Candidate source SHA-256: 95bba0be4c59445eca0ca72c16c4b486c0737befd49ab0e60716a2c112d818ad.
- Matrix runner SHA-256: 13e8b219f7767c3aea34ec46c090190d08aa79b937a46d37f62ef222119c4789.
- Focused test SHA-256: dee635b6576430f20aede95ad0971d135f6a1d075ba28899875cb6379aceba7e.
- Producer report SHA-256: 3dc04915443c9abf682a81c5c4e1c5b2eaa7030394514663331c48682a574dcc.

I independently enumerated the report tuples and confirmed all 256 unique
cursor x cached x mask combinations for cursor/cache 0..3 and four logical
input bits ordered as 5, 0xE, 6, 0xF. Every matrix row passed. The separate
script_not_ready and preview_not_ready cases both stopped at 0x001EA62C with no
trigger observations; all ready cases reached 0x001E9E50, after the pinned
load at 0x001E9E4C.

The comparison includes stop/fault state, readiness and trigger order/results,
event observations and selection/cache values at event time, the two work
blocks and singleton slot, r4-r11, d8-d15, FPSCR, s17, r6, SP equality and
alignment, and the published captured-pointer mailbox. The report first
mismatch is null. A private mutant replacing the pinned negative normalization
with raw signed remainder by 4 is rejected for cursor zero and trigger 5:
original selection/cache becomes 3, mutant selection becomes 0xFFFFFFFF, and
the event/work projections differ. The command and focused test exits are
recorded as zero in the handoff.

## Remaining limits and recommendation

This is stronger synthetic caller-window evidence for the existing editable
adapter candidate, not a production replacement. The synthetic frame starts at
the inline entry, so the callback prologue/epilogue are excluded. Readiness,
trigger and event internals are configured hooks; physical input and event
queue work are absent. The success path stops after the first touch-pointer
reload, and cursor/cache inputs are limited to 0..3. Production placement,
full callback behavior, live object/binding, rendering, and Azahar/game runtime
are not established. Caller-saved scratch registers/flags and arbitrary process
memory are outside the report projection.

Recommendation: accept the corrected matrix as partial experimental evidence
after this review, supersede the old differential claim, and leave production
integration pending a separate caller/runtime task.
