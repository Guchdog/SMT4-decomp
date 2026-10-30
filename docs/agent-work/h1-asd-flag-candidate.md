# `h1-asd-flag-candidate` handoff

## Result

The pinned routine at `0x002C00D4` is an 18-byte executable Thumb body inside a
20-byte `matching` ledger span. It performs a 32-bit test-and-set on the word
pointed to by `r0`: nonzero returns zero without a write; zero stores one and
returns one. The trailing `0xFFFF` at `0x002C00E6` is not executed; both branches
return through `bx lr` at `0x002C00E4`. This is an ordinary single-threaded
memory operation, not an atomic synchronization primitive.

## Implementation and scope

The readable experimental candidate is in
`experiments/semantic_equivalence/h1_asd_flag_candidate.cpp`. It uses a normal
32-bit pointer load/store and return value. The exact ledger remains `matching`
and no production file was changed. Caller cross-checks find ARM `BLX` sites at
`0x001099B4`, `0x001F6948`, and `0x0036C380`; each compares returned `r0` with
zero before one-time initialization.

The private runner builds the candidate and an intentionally wrong
missing-store control with one compiler at a time, executes the pinned original
in Thumb state and candidates in ARM state on ARM11 MPCore, and compares return
value, callee-saved registers/SP, d8-d15, data/stack, and read/write footprints.
Directed values cover zero, one, positive, high-bit, `0xffffffff`, signed
minimum, and signed maximum, with seeded word-aligned offsets and surrounding
bytes. The report and hashes are under this packet's private run root.

## Evidence limits

This is focused ordinary-RAM differential evidence, not a formal proof,
captured gameplay trace, concurrency test, H1 runtime-selection test, production
integration, or boot. Pointers must be valid and word aligned. Unaligned and
invalid-pointer behavior is excluded; caller-saved registers and NZCV are not
compared because observed callers test `r0` after the call. The ledger's
`matching` label is preserved, but the semantic candidate is not claimed to be
byte-identical.

See the structured `handoff.json` and hashed `report.json` beside this note in
the private output root for exact commands, case results, and artifact identity.
