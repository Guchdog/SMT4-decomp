# H1 type-0 callback candidate handoff

Task `h1-type0-callback-candidate` isolates the callable ARM entry at
`0x0015555C`. The preceding routine returns at `0x00155558`; original callback
execution starts directly at the next instruction and terminates at its own
`bx lr` (`0x00155580`). Its registration literal and the H1 callback `BLX`
sites establish that this interior entry is used independently of the
preceding routine.

## Recovered contract

The recovered hard-float contract is `(lower=s0, upper=s1, value=s2) -> s0`.
There are no memory writes; `r4-r11`, `sp`, and `d8-d15` are preserved. The
original callback's compare order matters: `VCMPE(value, upper)` followed by
GT upper clamp and immediate return, then `VCMPE(result, lower)` followed by
LO lower clamp. For unordered VCMPE, `NZCV=0011`, so both ARM GT and LO are
false. A NaN value therefore reaches the second compare and remains unchanged
in `s0`. VCMPE still sets FPSCR invalid-operation status. The candidate keeps
only those compare/flag operations as inline VFP semantic primitives and
expresses the rest as readable C++.

## Validation

The isolated runner compares pinned original ARM with the compiled hard-float
candidate in fresh Unicorn machines. It compares exact returned `s0`, FPSCR,
callee-saved registers, SP, and data/stack effects. All 17 cases pass: ordinary
values, exact and over/under clamp boundaries, reversed and equal bounds, NaNs
in value and bound positions, infinities, and signed zero. The deliberately
wrong ordered-comparison negative control preserves the same result `s0` bits
for all four unordered cases, but differs in FPSCR because its quiet comparison
does not set the VCMPE invalid-operation status. The focused test suite passes
3/3.

Private report and ARM object:
`build/agent-work/H1-semantic/h1-type0-callback-semantic-correction/overnight-20261025-type0-callback-correction/run-02/`.
For all four unordered controls, `s0` matches bit-for-bit while FPSCR differs:
the deliberately quiet comparison omits the VCMPE invalid-operation status.
The structured correction handoff records artifact hashes and exact commands/exits.

## Evidence limits

Caller reachability is supported by static registration/call-site evidence and
prior synthetic H1 traces that execute this original callback. The live title
source object's type byte and callback target remain unknown. No emulator,
renderer, integrated caller C++, or whole-game behavior was tested.

Next: independent review of the entry boundary, VFP NaN/FPSCR treatment, and
17-case differential before any integration task.
