# `0x002C0EC4` Tbb_GetGlobalSubTable production conversion

**Result:** typed C++ replacement for `Tbb_GetGlobalSubTable` at `0x002C0EC4` in `src/ui/tbb_loader.cpp`, validating bounded contract, boundary behavior, callee delegation, and caller composition through `0x002AEA28`.

## Contract and implementation

The pinned function at `0x002C0EC4` (28 bytes) receives `(u32 slot_id, u32 table_index)`.
It compares `slot_id` against unsigned limit `0x43` (67 decimal).
- If `slot_id < 0x43u`: loads the container pointer from `0x0049382C + slot_id * 16 + 4` (`0x00493830 + slot_id * 16`).
- If `slot_id >= 0x43u`: clears `container` to `nullptr` (`0`).
- It preserves `table_index` in `r1` and tail-calls `Tbb_GetSubTable(container, table_index)` at `0x002AC2F4`.

The typed C++ implementation in `src/ui/tbb_loader.cpp` is:

```cpp
// DECOMP_FUNC(0x002c0ec4, 28)
__attribute__((minsize)) const Tbl1Header* Tbb_GetGlobalSubTable(u32 slot_id, u32 table_index) {
    const TbcrHeader* container = nullptr;
    if (__builtin_expect(slot_id < 0x43u, 1)) {
        container = *reinterpret_cast<const TbcrHeader* const*>(0x00493830u + slot_id * 16);
    }
    return Tbb_GetSubTable(container, table_index);
}
```

The compiled body occupies exactly 28 bytes (7 ARM instructions/words), contains a single unconditional branch relocation to `Tbb_GetSubTable`, and fits into the original 28-byte slot with zero bytes of padding or overflow.

## Validation

| Check | Result |
| --- | --- |
| Final-VMA direct differential | 130/130 cases; 0 mismatches across registers `r0`, `sp`, `r4`–`r11`, memory writes, and callee arguments |
| Caller composition (`0x002AEA28`) | 7/7 profile index cases (`0`, `1`, `5`, `15`, `16`, `20`, `0xFFFFFFFF`); matched identically |
| Mutation controls | 3/3 detected: `wrong_boundary_43` (boundary off-by-one), `wrong_base_offset` (base pointer offset), and `return_non_null_out_of_bounds` (out-of-bounds sentinel) |
| Slot and IPS replay | 28/28 bytes; single-slot IPS roundtrip verified with byte-for-byte fidelity |
| Compilation | Compiled cleanly with Clang ARMv6K (`--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2`) |

Because the Clang compiler emits semantically equivalent instructions (`cmp r0, #0x42; ldrls ...; movhi r0, #0; lslls ...; ldrls ...; b ...`) rather than historical byte-identical instructions, the ledger row in `config/functions.csv` is truthfully classified as `non_matching`.
