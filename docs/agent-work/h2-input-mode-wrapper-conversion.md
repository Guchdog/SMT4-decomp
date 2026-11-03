# H2 mode predicate partial-span conversion — 2026-11-02

Converted the predicate at `0x00128C2C` to typed C++ while retaining the separately callable interior service stream in the 84-byte ledger span. The wrapper calls the validated unsigned-byte getter `0x00138F34`, compares the full result to 4, and returns exactly 1 or 0. The production wrapper body occupies 24/24 bytes; its single ARM call relocation resolves to the even getter entry.

The interior `func_00128c48` compiles to the exact original 56 bytes at `0x00128C48..0x00128C7F`. The staged image patches only the first 24-byte wrapper window and the 16-byte getter slot; `0x00128C44..0x00128C7F` is preserved byte-for-byte, including the NOP, both interior branch targets and literal pool. The whole 84-byte ledger span is `non_matching` because the wrapper portion differs.

Offline final-VMA checks passed all 256 mode-byte inputs, testing raw returns, SP and `r4-r11`. Fourteen compositions through original `0x0011C5EC` covered modes `0, 3, 4, 5, 0x7f, 0x80, 0xff` with ring counts 0 and 1; mode 4 suppresses ring reading while other modes continue. The reader-to-wrapper, wrapper-to-getter, and two direct tail branches to preserved interior addresses were verified. A wrong comparison constant mutation was detected. One-slot partial-window IPS replay passed.

Coordinator report: `build/agent-work/H2-semantic/h2-input-mode-wrapper-00128c2c-convert/run001/coordinator/report.json`; runner: `tools/h2_input_mode_wrapper_experiment.py`.

This verifies the wrapper predicate and preserves, but does not execute or validate, SVC `#0x32` kernel effects. Physical mode meaning/provenance, handle lifetime, scheduling, and full H2 runtime are outside this evidence.
