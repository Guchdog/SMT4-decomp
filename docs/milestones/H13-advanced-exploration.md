# Milestone H13: Advanced Exploration, Minimap, and Overworld

- **Status:** COMPLETED
- **Workflow Board:** `config/agent-workflows/h13.json`
- **Cumulative Staged Binary:** `build/agent-work/H13-semantic/h13-integrated-stage/code.h13-final.bin`
- **LayeredFS Mod IPS:** `build/agent-work/H13-semantic/h13-integrated-stage/code.h13-final.ips`

## Overview
Milestone H13 reconstructs and verifies the core exploration, minimap, and overworld navigation logic of Shin Megami Tensei IV:
1. Place window banner visibility state update (`PlaceWin_SetVisible`, `0x002638FC`).
2. Place window banner dismissal and state transition to inactive (`PlaceWin_Dismiss`, `0x002638DC`).
3. Place window banner timer duration and activity state evaluation (`PlaceWin_IsActive`, `0x0026394C`).
4. Exploration field active flag clearing and reset (`MapField_ClearActiveFlag`, `0x00208A70`).
5. Minimap navigation marker target coordinates configuration (`MapNavi_SetTargetCoords`, `0x001D2E24`).
6. Minimap navigation system state reset and runtime buffer synchronization (`MapNavi_Reset`, `0x001D2E0C`).
7. Map particle effect scaling calculation based on viewport distance and level parameters (`MapEpl_CalcScale`, `0x00193B28`).
8. Overworld entity Euclidean distance computation using hardware VFP square root (`MapCalc_DistanceToEntity`, `0x001D3A9C`).

## Footprint Summary
- Total window allocated: 240 bytes
- Total candidate compiled: 236 bytes
- Total headroom margin: +4 bytes (0 overflows across all 8 functions)

## Verification Proof
- All 8 candidates passed Unicorn ARM differential simulation against original machine code with 100% register and memory parity.
- Mutation probes verified sensitivity for every subsystem.
- Cumulative staging over H12 baseline verified with round-trip IPS fidelity.
