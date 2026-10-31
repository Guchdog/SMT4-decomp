# H20 Platform Abstraction Layer (HAL) Architecture Reconnaissance Record

- **Milestone:** H20 (Platform Abstraction Layer & Portability / Capa de Abstracción de Plataforma HAL y Portabilidad Nativa)
- **Scope:** Decouple proprietary 3DS kernel/SDK services (`nn::`, `fs`, `gsp`/`gx`, `dsp`, `hid`, `os`) behind portable, platform-agnostic HAL interfaces (`include/hal/`) and modular backends (`src/hal/`).
- **Subsystems Implemented:**
  1. System (`hal_system.h` / `hal_system.cpp`): Platform lifecycle, memory info, high-resolution monotonic clock.
  2. FileSystem (`hal_filesystem.h` / `hal_filesystem.cpp`): Virtual archive mounting, unified file streaming (`IFile`).
  3. Graphics (`hal_graphics.h` / `hal_graphics.cpp`): Dual-screen display targets, stereoscopic 3D presentation, VSync.
  4. Audio (`hal_audio.h` / `hal_audio.cpp`): Multi-channel PCM stream management, sample queueing, volume gain.
  5. Input (`hal_input.h` / `hal_input.cpp`): Circle Pad analog stick, touchscreen coordinates, digital button states.
- **Verification:** 100% passed autonomous verification suite (`tools/verify_h20_hal.py`) and clean Clang ARMv6K compilation (`tools/build_h20_all.py`).
