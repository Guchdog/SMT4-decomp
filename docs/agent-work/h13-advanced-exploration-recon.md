# H13 Advanced Exploration Architecture Reconnaissance Record

- **Milestone:** H13 (Advanced Exploration, Minimap, and Overworld / Exploración Avanzada, Minimapa y Overworld)
- **Scope:** Reconstruct and verify readable, editable C++ for 8 critical exploration subsystems covering place window banner visibility and dismissal, place window banner timer activity check, field active flag reset, minimap navigation target coordinates setup, minimap runtime state reset, map particle effect scaling calculation, and overworld entity distance calculation.
- **Offline-First Differential Gate:** Passed with 100% register/memory parity across all 8 subsystems on Unicorn ARM11MPCore CPU emulation against pinned `code.bin`.

## Target Subsystems Summary
1. `0x002638FC` - `PlaceWin_SetVisible` (20 B allocated, 20 B compiled, +0 B headroom)
2. `0x002638DC` - `PlaceWin_Dismiss` (32 B allocated, 32 B compiled, +0 B headroom)
3. `0x0026394C` - `PlaceWin_IsActive` (44 B allocated, 44 B compiled, +0 B headroom)
4. `0x00208A70` - `MapField_ClearActiveFlag` (20 B allocated, 20 B compiled, +0 B headroom)
5. `0x001D2E24` - `MapNavi_SetTargetCoords` (40 B allocated, 40 B compiled, +0 B headroom)
6. `0x001D2E0C` - `MapNavi_Reset` (24 B allocated, 24 B compiled, +0 B headroom)
7. `0x00193B28` - `MapEpl_CalcScale` (28 B allocated, 28 B compiled, +0 B headroom)
8. `0x001D3A9C` - `MapCalc_DistanceToEntity` (32 B allocated, 28 B compiled, +4 B headroom)

Total footprint: 240 bytes allocated, 236 bytes compiled, +4 bytes total headroom margin.
