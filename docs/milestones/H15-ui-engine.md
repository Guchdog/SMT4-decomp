# Milestone H15: UI Engine, Fonts, and 2D Rendering

- **Status:** COMPLETED
- **Workflow Board:** `config/agent-workflows/h15.json`
- **Cumulative Staged Binary:** `build/agent-work/H15-semantic/h15-integrated-stage/code.h15-final.bin`
- **LayeredFS Mod IPS:** `build/agent-work/H15-semantic/h15-integrated-stage/code.h15-final.ips`

## Overview
Milestone H15 reconstructs and verifies the core 2D user interface, fonts, dialog states, and context management logic of Shin Megami Tensei IV:
1. UI text formatting control field 0x10 configuration (`UiText_SetCodeField10`, `0x0010E570`).
2. UI text formatting control field 0x28 configuration (`UiText_SetCodeField28`, `0x0010E5BC`).
3. UI dialog active state and result code retrieval (`UiDialog_GetState`, `0x00126084`).
4. UI dialog header bitmask flags inspection (`UiDialog_GetFlags`, `0x001260A8`).
5. UI dialog selection cursor index position query (`UiDialog_GetCursorIndex`, `0x00126220`).
6. UI text draw buffer horizontal coordinate retrieval (`UiText_GetDrawCoordX`, `0x00126628`).
7. UI text draw buffer vertical coordinate retrieval (`UiText_GetDrawCoordY`, `0x00126638`).
8. UI manager active context instance handle lookup (`UiManager_GetContextHandle`, `0x0026B844`).

## Footprint Summary
- Total window allocated: 128 bytes
- Total candidate compiled: 128 bytes
- Total headroom margin: +0 bytes (exact 100% window match, 0 overflows across all 8 functions)

## Verification Proof
- All 8 candidates passed Unicorn ARM differential simulation against original machine code with 100% register and memory parity.
- Mutation probes verified sensitivity for every subsystem.
- Cumulative staging over H14 baseline verified with round-trip IPS fidelity.
