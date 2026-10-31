# Contract Specification for SaveLoadProcess_Write (0x002EFB50)

- **Target Address:** 0x002EFB50
- **Original Footprint:** 456 bytes
- **Subsystem:** Milestone H6 Persistence Logic (SaveLoad process state serialization and slot write)

## Functional Specification
Reconstructs complete semantic behavior of `SaveLoadProcess_Write` in readable, editable C++. Preserves registers `r4-r11`, `sp`, and respects 3DS ARMv6K AAPCS ABI conventions.
