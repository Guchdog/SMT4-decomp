# H14 ASD Graphics Engine Architecture Reconnaissance Record

- **Milestone:** H14 (ASD Graphics Engine: Scene, 3D Models, Textures, Effects / Motor Gráfico ASD: Escena, Modelos 3D, Texturas y Efectos)
- **Scope:** Reconstruct and verify readable, editable C++ for 8 critical graphics subsystems covering particle effect state locking and restoration, resource context resolution, GPU heap querying, text engine shader code setup, and texture streaming queue comparison.
- **Offline-First Differential Gate:** Passed with 100% register/memory parity across all 8 subsystems on Unicorn ARM11MPCore CPU emulation against pinned `code.bin`.

## Target Subsystems Summary
1. `0x00152D7C` - `AsdEffect_LockEnter` (48 B allocated, 44 B compiled, +4 B headroom)
2. `0x00152DAC` - `AsdEffect_LockLeave` (56 B allocated, 56 B compiled, +0 B headroom)
3. `0x002C31BC` - `AsdRes_GetContext` (28 B allocated, 28 B compiled, +0 B headroom)
4. `0x002C3B88` - `AsdGpu_HeapSize` (16 B allocated, 16 B compiled, +0 B headroom)
5. `0x0010A6FC` - `AsdText_SetCodeField1C` (16 B allocated, 16 B compiled, +0 B headroom)
6. `0x0010AF38` - `AsdText_SetCodeField14` (16 B allocated, 16 B compiled, +0 B headroom)
7. `0x0010B340` - `AsdText_SetCodeField30` (16 B allocated, 16 B compiled, +0 B headroom)
8. `0x003878C0` - `TextureStreamer_Compare` (16 B allocated, 16 B compiled, +0 B headroom)

Total footprint: 212 bytes allocated, 208 bytes compiled, +4 bytes total headroom margin.
