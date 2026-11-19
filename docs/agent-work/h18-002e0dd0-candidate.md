# Bounded candidate: 0x002e0dd0

**Owner:** `h18_wrapper_impl`

**Outcome:** Ready for independent review as a modeled wrapper candidate, not a full semantic reconstruction.

## Files and implementation

- `experiments/semantic_equivalence/h18_002e0dd0_candidate.cpp` implements only the callable body ending at `0x002e0e58`.
- The candidate has the exact five-scalar-argument C ABI. It reads the global/object pointer chain, calls the pinned typed helper interfaces in the recovered sequence, preserves the bit-31 gate and `{0,5}` return, and forwards `arg4` to the second value helper.
- `0x002e0e5c` and the remainder of the 724-byte catalog span are not interpreted or modified. No production source or ledger was changed.

## Evidence

- Runner: `tools/h18_002e0dd0_experiment.py`; candidate function has no ELF relocations and its local branch/literal references are validated before injection.
- Differential runs use the pinned original `code.bin` and the compiled candidate with the same four hooks: gate, Thumb halfword-count helper, value helper, cleanup helper.
- Covered behavior: bit31 gate with five boundary values; terminated halfword buffers including empty, singleton, mixed/high-bit and several-unit sequences; helper call count/order/arguments; return 0 or 5; the fifth stack argument; caller windows for the ignored-result caller and both return branches of `ui_func_003bbfb0`.
- Negative controls compile deliberate mutants for gate semantics, key `0x6e`, and the fifth-argument forward. Each must be detected.
- Reports and command details are in run-001 handoff; this models dependency behavior and does not establish helper semantics.

## Caller composition

- `ui_func_003bbdb8` begins at BL `0x003bbdfc`; after the wrapper returns, it overwrites `r0` and continues to its next helper call.
- `ui_func_003bbfb0` begins at BL `0x003bc070`; its exact comparison maps return 5 to `0x11` and non-5 to 0 (`bne 0x003bc02c`, the stack adjustment before the epilogue). Both complete caller return paths are composed. The `mov r0,#0x81` at `0x003bc028` lies before and is skipped by the branch target.

## Limits and next action

The helper/global object semantics remain unresolved. Caller setup before the BL sites and application state are not executed. The second body beginning at `0x002e0e5c` remains unassigned/unresolved. Review the C++ ABI, gate semantics, helper stubs and two seeded reports; then decide whether further dependency recon is needed before any promotion.
