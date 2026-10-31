# H15 UI Engine, Fonts, and 2D Rendering Architecture Reconnaissance Record

- **Milestone:** H15 (UI Engine, Fonts, and 2D Rendering / Motor de UI, Fuentes y Renderizado 2D)
- **Scope:** Reconstruct and verify readable, editable C++ for 8 critical UI and font engine subsystems covering text formatting control codes, dialog state query, dialog flags inspection, dialog cursor index retrieval, text coordinate calculation, and context manager handle lookup.
- **Offline-First Differential Gate:** Passed with 100% register/memory parity across all 8 subsystems on Unicorn ARM11MPCore CPU emulation against pinned `code.bin`.

## Target Subsystems Summary
1. `0x0010E570` - `UiText_SetCodeField10` (16 B allocated, 16 B compiled, +0 B headroom)
2. `0x0010E5BC` - `UiText_SetCodeField28` (16 B allocated, 16 B compiled, +0 B headroom)
3. `0x00126084` - `UiDialog_GetState` (16 B allocated, 16 B compiled, +0 B headroom)
4. `0x001260A8` - `UiDialog_GetFlags` (16 B allocated, 16 B compiled, +0 B headroom)
5. `0x00126220` - `UiDialog_GetCursorIndex` (16 B allocated, 16 B compiled, +0 B headroom)
6. `0x00126628` - `UiText_GetDrawCoordX` (16 B allocated, 16 B compiled, +0 B headroom)
7. `0x00126638` - `UiText_GetDrawCoordY` (16 B allocated, 16 B compiled, +0 B headroom)
8. `0x0026B844` - `UiManager_GetContextHandle` (16 B allocated, 16 B compiled, +0 B headroom)

Total footprint: 128 bytes allocated, 128 bytes compiled, +0 bytes total headroom margin (exact 100% binary fit).
