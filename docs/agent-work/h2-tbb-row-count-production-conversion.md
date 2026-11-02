# `Tbb_GetRowCount` (`0x002C0E4C`) production conversion

## Contract and implementation

The pinned routine returns zero for a null pointer, non-`TBL1` magic, or zero
row stride. For a valid header it returns the unsigned quotient
`payload_size / row_stride` by tail-branching to the existing ARM divider
`ui_func_002c6c10`. The C++ implementation preserves this helper and its
argument order. The 56-byte body fits its original slot; the branch relocation
targets the even ARM entry at `0x002C6C10`.

## Validation

| Check | Result |
| --- | --- |
| Direct final-VMA differential | 13/13 cases; zero mismatches |
| H2 selector composition | 5/5 cases through original `0x002AEA28` with converted row-count helper |
| Mutation controls | 3/3 detected: magic polarity, zero-stride boundary, swapped divider operands |
| Body and placement | 56/56 bytes; one ARM tail-branch relocation; slot-only IPS replay passed |
| Affected TU builds | `tbb_loader.cpp`, `leaf_batch24_b.cpp`, `leaf_batch32_c.cpp`: 3/3 passed |

The fixtures cover null and unmapped table pointers, bad magic, zero stride,
zero payload size, representative integer quotients and high unsigned values.
The divider entry observed `r0=payload_size`, `r1=row_stride`, with eight-byte
stack alignment. The selector compositions use a synthetic but structurally
valid global slot, TBCR container, and TBL1 child table.

The object file contains a branch relocation placeholder at offset 40. Once
resolved to `0x002C6C10`, the complete 56-byte final-VMA body is byte-identical
to the pinned function. Its ledger status therefore remains `matching`. The
original divider and all other TBB services remain in the image. Live resource
population, arbitrary invalid-memory domains, downstream profile validity,
audio, and runtime behavior are not established.

Independent review approved the bounded contract and final-VMA classification:
[review report](h2-tbb-row-count-independent-review-002c0e4c.md).

Raw report and IPS are under
`build/agent-work/H2-semantic/h2-tbb-row-count-convert-002c0e4c/run002/checks/direct-final/`.
