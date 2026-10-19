# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation Progress

## Overall `.text` Progress

| Metric | Decompiled | Total | Remaining | Percentage |
|--------|-----------:|------:|----------:|-----------:|
| **Code Size (Bytes)** | 572 B | 3,139,108 B | 3,138,536 B | **0.0182%** |
| **Functions** | 8 | 10,349 | 10,341 | **0.0773%** |

## Subsystem Breakdown

| Subsystem | Decompiled Funcs | Total Funcs | Decompiled Bytes | Total Bytes | Subsystem % |
|-----------|-----------------:|------------:|-----------------:|------------:|------------:|
| `engine` | 0 | 2,372 | 0 B | 737,192 B | 0.000% |
| `ui` | 6 | 1,177 | 500 B | 654,800 B | 0.076% |
| `unknown` | 0 | 3,829 | 0 B | 654,752 B | 0.000% |
| `script_vm` | 0 | 1,230 | 0 B | 461,272 B | 0.000% |
| `camp` | 0 | 944 | 0 B | 346,544 B | 0.000% |
| `battle` | 0 | 566 | 0 B | 220,356 B | 0.000% |
| `shop` | 0 | 110 | 0 B | 36,576 B | 0.000% |
| `crt` | 2 | 26 | 72 B | 9,484 B | 0.759% |
| `unite` | 0 | 31 | 0 B | 9,280 B | 0.000% |
| `nn_sdk` | 0 | 64 | 0 B | 8,852 B | 0.000% |

## Decompiled Functions Ledger

| Address | Size (Bytes) | Category | Status | Symbol Name | Source File |
|---------|-------------:|----------|--------|-------------|-------------|
| `0x00100000` | 36 | `crt` | `non_matching` | `__start` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x00100024` | 36 | `crt` | `non_matching` | `__init_bss` | [`src/crt/start.cpp`](src/crt/start.cpp) |
| `0x0010299c` | 260 | `ui` | `non_matching` | `IfTouch_Init` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002ac2f4` | 92 | `ui` | `non_matching` | `Tbb_GetSubTable` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e4c` | 56 | `ui` | `non_matching` | `Tbb_GetRowCount` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e84` | 24 | `ui` | `non_matching` | `Tbb_GetDefaultTable18Payload` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0e9c` | 40 | `ui` | `non_matching` | `Tbb_GetPayloadData` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
| `0x002c0ec4` | 28 | `ui` | `non_matching` | `Tbb_GetGlobalSubTable` | [`src/ui/tbb_loader.cpp`](src/ui/tbb_loader.cpp) |
