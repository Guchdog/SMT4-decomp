# Independent review: `TitleConfig_Calc` wrap semantics

## Review result

No blocking defect found in the defined-u32 correction or its bounded
callback/final-address evidence. The candidate now matches the original ARM
32-bit register arithmetic at the `0x002C615C` helper boundary for the tested
signed helper-result bit patterns. Accept this as an experimental arithmetic
correction; do not treat it as production promotion or whole-H2 equivalence.

## Arithmetic review

The original operations are 32-bit register subtraction, multiply by five, and
doubling. The candidate converts both `s32` helper returns to `u32` before
subtraction, then performs the multiplications as `u32`. Because the target is
32-bit ARM and `u32` is `unsigned int`, C++ defines all three steps modulo
`2^32`, with no signed-overflow undefined behavior. Passing `u32` values to the
helper preserves their bits in `r0` and `r2`; converting the `s16` limit to
`u32` preserves the existing sign-extended `r1` word.

The four directed cases use valid signed 32-bit helper returns and keep the
mocked helper's mapped result in the initialized option range:

| Case | Script/current helper returns | Expected `(r0,r1,r2)` words | Mock return |
|---|---|---|---:|
| max minus min | `INT32_MAX`, `INT32_MIN` | `0xfffffff6, 10, 0xfffffffb` | 3 |
| min minus max | `INT32_MIN`, `INT32_MAX` | `10, 10, 5` | 7 |
| positive scale edge | `INT32_MAX`, `0` | `0xfffffff6, 10, 0x7ffffffb` | 10 |
| negative scale edge | `INT32_MIN`, `0` | `0, 10, 0x80000000` | 0 |

The callback comparator compares the ordered call trace as well as return,
register preservation, work bytes, and config bytes. Each callback report records
the original `bounded_value` argument tuple; a passing comparator means the
candidate trace matched those words exactly. The final-address comparator also
compares call traces for each original-vs-patched case.

## Report and artifact checks

All run-002 frozen input hashes matched. The four run-001 report hashes also
match the review packet's frozen inputs. Both callback reports use the same
candidate source hash `16f2af7c953a089ffe277d2f299ea89ab90d028f57d6708ffdc8cf6115844ed2`,
runner hash `f70429ef3cb9e186bb5d78863aade9e1d8e4a4262108bba33c48c334b8b71aac`,
test hash `b80719b01a4b17829aaac03ebabcb9504593a425b3e82e0993e703b71bb45fc3`,
and ARM object hash `cd4c0eb1cbf21ac849f994370c0403fb2a6919b0263afd834db5928e768c60b8`.

- Callback seed 7: 68/68; config-byte `+3` corruption control detected.
- Callback seed 20261024: 68/68; config-byte `+3` corruption control detected.
- Final-address patch seed 7: 68/68; branch-to-cave-plus-four control detected.
- Final-address patch seed 20261024: 68/68; branch-to-cave-plus-four control detected.

Both patch manifests report a 2,096-byte candidate with the same patched image
hash `c9ebf62679043512c22c684b50f9e9cbf1fe824e016f119c2de4bddf664eb45d` and
IPS hash `0b671f4f40c172984e730d0387899ce47abe8f2ee5e90043a2e481aa591cf781`.
The unchanged ARM object is consistent with the source-only semantics fix: the
compiler already emitted modulo register operations, while the C++ source now
expresses them without undefined signed overflow.

A current `check-handoff` rerun against the implementation's run-001 handoff
returns `Task assignment or scope changed since dispatch`; that old lease check
is stale under the current coordinator board. The run-001 handoff hash itself
matches this review packet's frozen input, and the fresh differential reports
match their frozen hashes. This does not change the bounded review conclusion.

## Evidence boundary

Real helper domains/semantics, caller composition, UI/input behavior,
changed-option exit behavior, persistence/re-entry, and Azahar runtime remain
unproven. The safe mapped return values validate the arithmetic arguments
without claiming real `bounded_value` behavior. No caller, emulator, RSP,
keyboard/mouse, or host-input test was performed in this review. Keep the
candidate experimental; production promotion still requires independent caller,
integration, persistence, and scoped runtime evidence.

