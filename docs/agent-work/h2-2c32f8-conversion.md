# TitleConfig sprite-group binder conversion — `0x002C32F8`

## Result

Replaced the 76-byte naked ARM body in `src/engine/leaf_batch13_b.cpp` with typed C++. The signature keeps the first four words in registers and seven opaque 32-bit values on the stack. The body is exactly 76 bytes and has no relocations. It returns `group+0x14`, matching the original raw `r0`, though known callers ignore that result. The compiled bytes differ, and the ledger is classified `non_matching`.

## Offline differential

The pinned original and one-slot staged candidate passed 51 direct cases: three directed cases and 48 seeded cases. Cases cover TitleConfig's exact tuple, high-bit/raw payload values, low-halfword truncation, and poisoned descriptor memory including the untouched bytes `+0x0A..+0x0B`. The runner independently calculates expected bytes, checks raw return and preserved GPR/VFP state/SP, replays the slot-only IPS, and verifies no changes outside the 76-byte span.

The original caller slice `0x002F4D34..0x002F4D6C` passed with the pinned group initializer followed by the candidate binder, reproducing the exact TitleConfig descriptor setup. A negative control that replaces the count halfword store with a NOP was detected. No emulator was run.

## Limits and remaining checks

The candidate compiles to the same slot size, but the compiler changes the ordering of independent stores relative to the original. The supported domain is aligned ordinary RAM with no concurrent observers or MMIO semantics. The table pointer/count are copied as descriptor fields; table contents and visible rendering are not established. The independent fresh-seed review passed 67 direct cases plus the caller slice and negative control. The full ARMv6K build passed 204/204 translation units. The caller ignores the raw return; the table semantics, rendering, runtime and full H2 lifecycle remain unverified.
