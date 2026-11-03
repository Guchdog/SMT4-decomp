# H2 getter conversion: `0x00289640`

## Implementation

Replaced the 20-byte naked ARM wrapper in `src/engine/leaf_batch21_b.cpp` with
typed C++ `u32 engine_func_00289640(u32 input)`. The raw input is ignored. The
implementation reads the pointer at `0x0044DEB8` and returns the 32-bit word at
pointer `+0xD0`. It has no writes or calls. The original literal `0x0044DE98`
was folded into a direct literal `0x0044DEB8`; the body remains 20 bytes, but
two slot words differ, so the truthful ledger status is `non_matching`.

## Offline differential

Command:

```text
python -B tools/h2_89640_experiment.py --out build/agent-work/H2-semantic/h2-callback-getter-00289640-convert/run001/checks/seed-20261113 --seed 20261113
```

Exit 0. The report is
`build/agent-work/H2-semantic/h2-callback-getter-00289640-convert/run001/checks/seed-20261113/report.json`.
All 40 direct original-versus-production cases and five original callback
compositions matched. Direct cases include zero, one, low/high boundaries,
`0x80000000`, `0xFFFFFFFF`, and 32 seeded values. Each compares ordered reads,
all writes, `r0`, `r4-r11`, SP/LR and the global/state memory. The actual
`0x00221168` callback executes the getter twice per composition; its other
getters and final helper are controlled stubs, and original `0x0028DF3C`
executes. The callback event trace confirms the two getter hits and the exact
six arguments reaching the final-helper stub. A compiled wrong-offset `+0xD4`
mutant is detected.

The production body is 20 bytes with no relocations; it differs from the pinned
slot at `0x00289644` and `0x00289650` because C++ folds the literal address.
The affected TU compiled, then the full ARMv6K build passed 204/204 TUs. Static
interworking checked the callback's two ARM BL targets to the even getter entry
and its `BX LR` return. This is semantic evidence for mapped ordinary RAM, not
proof of arbitrary alias/fault behavior or natural H2 state. No emulator was
used.
