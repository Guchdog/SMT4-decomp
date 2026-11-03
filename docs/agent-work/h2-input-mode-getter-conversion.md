# H2 input-mode byte getter conversion — 2026-11-02

Converted `0x00138F34` from naked assembly into a typed C++ volatile unsigned-byte getter at `0x0047388B`. The original 16-byte function uses `LDRB` from `0x00473888 + 3`, so it returns the raw unsigned value in `r0`. Original wrapper `0x00128C2C` compares that return with 4; the actual reader `0x0011C5EC` exits early only for that mode value.

The offline final-VMA differential passed all 256 byte values, checking raw return, SP and `r4-r11`. Fourteen compositions through the pinned original reader compared caller-visible state, writes, ring-helper behavior and getter call traces over modes `0, 3, 4, 5, 0x7f, 0x80, 0xff` with ring result counts 0 and 1. Mode 4 suppressed the ring helper; all other values continued into it. The wrapper's BL at `0x00128C30` and the reader-to-wrapper ARM call target were checked. A signed-byte mutation was detected. The final-VMA body is 16/16 bytes with no relocations; two-slot IPS validation is not relevant because only this one slot was patched, and exact one-slot IPS replay passed.

Coordinator report: `build/agent-work/H2-semantic/h2-input-mode-byte-getter-convert/run001/coordinator/report.json`; runner: `tools/h2_input_mode_getter_experiment.py`. The report pins the original image and records object, body, IPS and staged-image hashes.

Evidence is bounded to a mapped ordinary global and synthetic RAM through a controlled `0x0012A758` seam. It does not establish the physical purpose or origin of the byte, MMIO behavior, timing/scheduling, or full H2 runtime equivalence.
