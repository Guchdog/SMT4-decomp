# Contract Specification for Burroughs_GetSaveData (0x002A0FAC)

- **Target Address:** 0x002A0FAC
- **Original Footprint:** 24 bytes
- **Subsystem:** Milestone H10 Burroughs, Quests, and Apps (Burroughs and Quest save data pointer resolution from main game work)

## Functional Specification
Reconstructs complete semantic behavior of `Burroughs_GetSaveData` in readable, editable C++. Preserves registers `r4-r11`, `sp`, and respects 3DS ARMv6K AAPCS ABI conventions.
