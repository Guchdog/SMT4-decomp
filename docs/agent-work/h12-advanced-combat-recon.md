# H12 Advanced Combat Architecture Reconnaissance Record

- **Milestone:** H12 (Advanced Combat: Press Turn, Smirk, Negotiation, Results / Combate Avanzado: Press Turn, Smirk, Negociación y Resultados)
- **Scope:** Reconstruct and verify readable, editable C++ for 8 critical combat subsystems covering turn subsystems initialization, smirk condition query and slot exchange, turn phase data setup, battle result screen teardown and cleanup, unit defeat evaluation, and unit state buffer restoration.
- **Offline-First Differential Gate:** Passed with 100% register/memory parity across all 8 subsystems on Unicorn ARM11MPCore CPU emulation against pinned `code.bin`.

## Target Subsystems Summary
1. `0x00123050` - `Battle_InitTurnSubsystems` (64 B allocated, 60 B compiled, +4 B headroom)
2. `0x00129C58` - `Battle_GetUnitSmirkState` (24 B allocated, 20 B compiled, +4 B headroom)
3. `0x00129CBC` - `Battle_GetSmirkActor` (20 B allocated, 16 B compiled, +4 B headroom)
4. `0x00129C70` - `Battle_ExchangeSmirkSlot` (76 B allocated, 72 B compiled, +4 B headroom)
5. `0x00136FA4` - `Battle_InitTurnData` (40 B allocated, 40 B compiled, +0 B headroom)
6. `0x001C87D8` - `Result_Cleanup` (156 B allocated, 128 B compiled, +28 B headroom)
7. `0x0028DE4C` - `Battle_IsUnitDefeated` (56 B allocated, 44 B compiled, +12 B headroom)
8. `0x00215938` - `Battle_ResetUnitStateBuffer` (32 B allocated, 28 B compiled, +4 B headroom)

Total footprint: 468 bytes allocated, 408 bytes compiled, +60 bytes total headroom margin.
