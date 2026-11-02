# H2 `0x002BF6D0` conversion — indexed manager-node resolver

## Change

Replaced the 64-byte naked ARM body in `src/engine/leaf_batch27_b.cpp` with
typed C++. The implementation forwards both `group` and `node_index` to the
original `0x002B0188` resolver, gets the node base through the returned
manager's `+4` pointer chain, and returns the node address at
`node_base + 20*(node_index - 1000*(node_index/1000))`. Signed division
preserves truncation toward zero by calling original helper `0x002C615C`.
Integer address arithmetic retains 32-bit target wrap. The implementation
compiles to 60/64 bytes and resolves both calls to even ARM addresses.

## Validation

- Direct pinned-ARM differential: 2,269/2,269 cases matched, including the
  complete `[-1000,1000]` signed remainder sweep, signed endpoints, block
  boundaries and 256 seeded signed indices.
- Original caller composition through `0x002B88C4`: 42/42 cases matched with
  original `0x002B0188` executing and the resolved node record consumed.
- Three controls detected: wrong block divisor, dropped `node_index` forwarding,
  and wrong node stride.
- The candidate is 60 bytes in the 64-byte original slot; ARM relocations to
  `0x002B0188` and `0x002C615C` are even. Exact-slot IPS replay and one-slot-only
  audit passed.
- `leaf_batch27_b.cpp` and `leaf_batch32_c.cpp` compiled to private objects.

Primary report:
`build/agent-work/H2-semantic/h2-helper-002bf6d0-slot-fit-after-hidden-index/run003/checks/coordinator-seed-20261114/report.json`.

## Scope and limits

Direct cases use valid aligned synthetic memory and a deterministic resolver
return seam; the caller cases execute the original resolver and caller with a
controlled manager table. The original divider leaves stack spill bytes below
SP when called by the candidate; comparison excludes this temporary stack
residue while checking SP, preserved registers and all non-stack writes.
Malformed pointers, arbitrary aliasing, MMIO, manager lifecycle, live input
provenance and runtime behavior remain unverified. Independent review is
required before promotion.
