# H18 candidate report: enclosing handler `0x00207FFC`

Owner: `luna_cpp`  
Outcome: bounded candidate ready for independent review; caller and real helper
semantics remain open.

## Entry and ABI

The catalog label at `0x002080E0` is a branch target inside this handler. The
callable body starts at `0x00207FFC` and ends at `0x00208314`; the 704-byte
catalog interval also contains literal/string data and an independent short
routine at `0x0020835C`.

The entry saves `r4-r6,lr`, loads the pointer slot `0x004474D8` into `r4`, sets
`r6=0x63`, saves `d8`, allocates `0x98` stack bytes, then reads the context
pointer from `*(u32*)0x004474D8`. The visible body consumes no incoming argument
register: it initializes its state, floats, and helper inputs from globals,
context fields, or literals. Common return is zero; state `99` returns one.
Caller/dispatcher and runtime registration are not established.

## Handler behavior recovered

The signed halfword at `context+8` drives the state machine:

- `0`: if global word `0x0049FC7C` equals 1, clear `context+0x0C` and set state
  99. Otherwise either create/setup the embedded resource at `+0x28`, or resolve
  a sky ID from signed `+6`, format/load a sky path, increment state, and poll
  resource at `+0x10`. A ready resource is configured; when global-work halfword
  `+4` is `0x13`, an extra vector `(0,-20000,0)` is passed. Completed paths set
  state 10.
- `1`: poll resource at `+0x10`; on ready, configure it and optionally send the
  same extra vector for global-work `+4 == 0x13`, then set state 10.
- `10`: if `+0x20` is nonzero, create/setup an embedded resource from `+0x24` and
  set state 99. Otherwise normalize map IDs `0x29..0x2B` to `(0x24,1)`, or copy
  signed `+4` and unsigned `+6` to `+0x1C/+0x1E`; format/load a map path, save the
  handle at `+0x0C`, and increment state.
- `11`: poll `+0x0C`; on ready configure the resource and set state 99.
- `99`: return 1. All other signed states return 0 without changing state.

The candidate is `experiments/semantic_equivalence/h18_00207ffc_candidate.cpp`.
It calls the original helper addresses with observed register/stack argument
shapes and reads the original format strings from `0x00208328`/`0x00208340`.

## Validation

The focused runner compiles and stages local `R_ARM_ABS32` references without
changing shared build code. ARM-state original and candidate executions use the
same explicitly synthetic helper models. Cases cover clear/embedded/sky paths,
pending and ready polls, map IDs `0x29..0x2B`, signed map-ID boundaries, the
extra-vector gate, states `-1,0,1,10,11,12,99`, and seeded random combinations.
It compares the complete fixture data page and context, helper order/arguments
and formatted paths, return/continuation, stack restoration, callee-saved integer
registers, and `d8-d15`. The revision also lets helper stubs apply explicitly
configured post-call mutations to the context pointer, context fields, and
resource object fields.

- Independent review found a reload mismatch: when the `setup` model changed
  `*(context+0x10)` from `FILE_RESOURCE` to `ALLOC_RESOURCE`, the original
  reloaded the context slot before `set_a` and passed `RESOURCE_TARGET_A`
  (`33574912`), while the first candidate version retained the captured resource
  and passed `RESOURCE_TARGET_B` (`33579008`). The candidate now reloads the
  context pointer, resource slot, and resource `+8` target independently before
  each setter call, matching the original instruction sequence.
- Seed 7: 44/44 differential cases passed; all 3 negative controls detected.
- Seed 20261024: 44/44 differential cases passed; all 3 negative controls
  detected.
- `python -m unittest tests.test_h18_00207ffc_experiment -v`: passed.

Synthetic models configure the sky-ID result, allocation/load resource handles,
poll result, and record setup/float/vector calls. The formatter model writes only
the two known path formats. These models intentionally do not claim the real
helpers' ownership rules, side effects, readiness transitions, or general
formatter contract. Post-call mutations are test stimuli added to those models;
they demonstrate whether code follows the original's reload points and do not
show that real helpers mutate context or resource memory.
Generated report metadata states this distinction structurally: helper models
specify no context/resource writes by default (apart from the formatter's known
output-buffer write), while `post_call_fixture_mutation_policy` lists separate
fixture stimuli, their supported write kinds, and that they are not attributed
to helpers. The focused unit test asserts these descriptors and the setup
mutation event.

## Evidence limits and next action

Compiled and synthetic ARM differential evidence is bounded to valid mapped
objects and deterministic helper models. Real caller composition, helper
contracts, production integration, and runtime behavior are unverified. In
particular, the task did not establish who calls `0x00207FFC`; static searches do
not rule out computed, Thumb, unaligned, or runtime-created dispatch.

Next action: independent review the C++ branch mapping and runner stub models;
then recover the actual dispatcher and helper semantics before promotion or
runtime claims.
