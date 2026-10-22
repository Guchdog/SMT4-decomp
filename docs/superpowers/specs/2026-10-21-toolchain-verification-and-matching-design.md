# Shin Megami Tensei IV (`CTR-P-AMXE`) Toolchain, Disassembly Verification, and Byte-Matching Design

**Date:** 2026-10-21  
**Target Title:** *Shin Megami Tensei IV* (US, v0.1.0, Title ID `00040000000E5C00`, Product Code `CTR-P-AMXE`)  
**Repository:** `https://github.com/Guchdog/SMT4-decomp`

---

## 1. Intent and Why

To turn `SMT4-decomp` from an unverified draft reconstruction into a genuine, compilable 3DS C++ decompilation, four foundational upgrades are required:

1. **Real 3DS ARMv6K Compilation Pipeline:** Every C++ translation unit in `src/` must compile cleanly to 3DS ARMv6K (MPCore + VFPv2 hard-float) ELF object code (`.o`), catching header/type/offset errors automatically in the test suite.
2. **ARMv6K Assembly Diffing (`tools/asm_diff.py`):** A tool that compiles decompiled C++ functions to ARMv6K machine code, extracts the compiled `.text` bytes from the ELF object, and compares instructions and raw bytes directly against `extracted/exefs/code.bin`.
3. **Automated Disassembly Verification & Split Progress Metrics (`tools/verify_decomp.py` & `tools/progress.py`):** Progress reporting must separate **Matching (Byte-for-Byte)**, **Verified (ARMv6K Compiled & Disassembly-Checked)**, **Draft (`non_matching`)**, and **Scaffolded (`stub`)**, and forbid marking any function `matching` unless its compiled ARMv6K machine code matches `code.bin`.
4. **Leaf-First Byte-Matching Workflow (`tools/find_candidates.py` & initial `matching` batch):** A candidate finder that ranks small, self-contained leaf functions in `code.bin`, paired with an initial batch of leaf functions decompiled to 100% byte-for-byte `matching` status.

---

## 2. Goals, Non-Goals, and Anti-Goals

### Goals
- **100% TU Compilation (`tools/build_check.py`):** Fix all existing compile breaks across the 68 `.cpp` files in `src/` and compile every translation unit to `armv6k-none-eabihf` (`-mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -fno-exceptions -fno-rtti`) using freestanding C++ headers in `include/freestanding/`.
- **ELF32 ARM Object Diffing (`tools/asm_diff.py`):** Parse compiled ELF32 ARM `.o` files, match C++ symbols (mangled or `extern "C"`) to `config/functions.csv` entries, and compute exact byte match and instruction mnemonic match scores against `extracted/exefs/code.bin`.
- **Structural Disassembly Verification (`tools/verify_decomp.py`):** Verify that every claimed function compiles to ARMv6K, that `matching` functions are 100% byte-identical (up to relocatable branch targets), and that `non_matching` functions meet structural instruction/call thresholds to separate **Verified** from **Draft** reconstructions.
- **Leaf Candidate Ranking & First Byte-Matched Functions (`tools/find_candidates.py`, `src/engine/leaf_matching.cpp`):** Provide a CLI tool to discover small leaf functions and decompile an initial batch of leaf functions to verified `matching` status.

### Non-Goals
- Linking a complete bootable `.3ds`/`.cia` ROM today before the remaining ~9,900 functions are decompiled or sliced.
- Requiring proprietary licensed ARMCC binaries when LLVM/Clang `armv6k-none-eabihf` is installed locally and produces matching ARMv6K instructions on leaf/small functions.

### Anti-Goals
- Allowing broken `.cpp` files that do not compile to pass `unittest`.
- Allowing any function to be marked `matching` in `config/functions.csv` without automated verification against `extracted/exefs/code.bin`.
- Counting collapsed/dummy function bodies as verified decompilations.

---

## 3. Technical Architecture (Designer Calls)

1. **Compiler & Target Flags:**
   - Compiler: `C:\msys64\clang64\bin\clang++.exe` (auto-detected via `PATH` or standard MSYS2/LLVM paths).
   - Target flags: `--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -fno-exceptions -fno-rtti -ffreestanding -nostdinc -nostdinc++ -isystem include/freestanding -isystem <clang_resource_include> -Iinclude`.
2. **Freestanding Header Shim (`include/freestanding/`):**
   - Minimal freestanding headers (`cstddef`, `cstdint`, `cstring`, `cmath`, `algorithm`, `string.h`, `math.h`) wrapping Clang's builtin `<stddef.h>` and `<stdint.h>` so ARMv6K compilation never touches host Win32/MinGW headers.
3. **Pure-Python ELF32 ARM Parser in `tools/asm_diff.py`:**
   - Reads `.shstrtab`, `.symtab`, `.strtab`, `.rel.text`, and `.text` directly from compiled `.o` files using Python's `struct` module and `capstone`, avoiding fragile text parsing of `objdump`.
4. **Split Progress Categories in `tools/progress.py`:**
   - `matching`: 100% byte-verified ARMv6K compiled functions.
   - `verified`: `non_matching` functions that compile to ARMv6K and pass `verify_decomp.py` structural disassembly checks (compiled instruction ratio $\ge 0.25$ of binary instruction count or all `BL` call targets present).
   - `draft`: `non_matching` functions that compile to ARMv6K but have low structural coverage ($< 0.25$ instruction ratio) awaiting deeper pass.
   - `stub`: Scaffolded headers/skeletons.
