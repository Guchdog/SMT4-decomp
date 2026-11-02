# `camp_func_002b8794` (`0x002B8794`) production conversion

## Contract

The pinned entry accepts `(slot, priority, value, mode)`. It returns for
unsigned `slot >= 6` or a null manager pointer loaded from `0x0043DA2C`. In
nonzero mode it maintains two six-word registries at `0x0043DA50` and
`0x0043DA68`, including a reservation-byte search over `manager+0x4B8..0x4BD`
and a paired clear to `0xFFFFFFFF`. It then records a type byte and value
halfword in the manager slot and writes the row control fields selected by the
priority classes. The H2 wrapper at `0x002B8B78` calls this helper six times
with `mode=0`.

The C++ implementation uses typed arguments and explicit volatile field writes
to preserve their order. The compiled body occupies 272/304 bytes and has no
relocations. Its final body differs from the pinned ARM function, so the ledger
classification is `non_matching`.

## Validation

| Check | Result |
| --- | --- |
| Direct final-VMA differential | 12/12 cases; zero mismatches |
| Original caller slices | `0x99` TitleConfig init and `0xDC` nested callback both matched; each executed six actual calls |
| Mutation controls | 3/3 detected: slot boundary, priority-8 class, and registry mode |
| Body and placement | 272/304 bytes, no relocations, slot-only IPS replay passed |
| Affected TU builds | `leaf_batch41_a.cpp` and `leaf_batch32_c.cpp`: 2/2 ARMv6K builds passed |

Direct fixtures cover slots 0, 1, 2, 3, 4, 5, 6, and `UINT32_MAX`; null
manager; default/special priority classes; 16-bit value truncation; registry
claim, release, and no-claim branches. The comparison observes mapped manager
and global memory, ordered writes, SP, callee-saved registers, faults, and call
arguments. Caller slices execute original `0x002B8B78`, `0x002AEA28`, and TBB
services with structurally valid synthetic profile data; the other external
services are explicit hooks.

Manager storage and TBB data are synthetic ordinary-memory fixtures. The H2
wrapper evidence uses `mode=0`; nonzero-mode behavior is direct-fixture
evidence. This does not establish manager lifetime/concurrency, natural
callback reachability, actual audio output, or emulator/runtime behavior.

Raw report and slot IPS are under
`build/agent-work/H2-semantic/h2-profile-slot-registry-002b8794-convert/run001/checks/direct/`.

Independent review approved the bounded contract and `non_matching`
classification: [review report](h2-profile-slot-registry-independent-review-002b8794.md).
