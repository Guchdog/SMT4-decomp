# ARMv6K Toolchain, Disassembly Verification, Split Progress, and Byte-Matching Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish a 100% compiling 3DS ARMv6K (`armv6k-none-eabihf` MPCore + VFPv2) build pipeline across all translation units in `src/`, build an ELF32 ARM assembly diffing and disassembly verification engine (`tools/asm_diff.py` & `tools/verify_decomp.py`), split progress reporting into `Matching`, `Verified`, `Draft`, and `Stub` tiers, and decompile an initial batch of 12 leaf functions (184 bytes) to verified **100% byte-for-byte `matching`** status.

**Architecture:**
- `include/freestanding/*`, `tools/build_check.py`, `CMakeLists.txt`, and header fixes (`include/engine/asd_symbols.h`, `include/ui/status.h`, `src/ui/result.cpp`, `tools/split_asm.py`): fixes the 10 broken translation units and compiles all `.cpp` files in `src/` to 3DS ARMv6K ELF32 `.o` objects.
- `tools/asm_diff.py` & `tools/verify_decomp.py`: parses compiled ELF32 ARM `.o` objects, diffs compiled functions against `extracted/exefs/code.bin`, verifies `matching` functions are 100% byte-identical, and audits `non_matching` functions into `verified` vs `draft`.
- `tools/progress.py`, `tools/find_candidates.py`, `include/engine/leaf_matching.h`, and `src/engine/leaf_matching.cpp`: splits progress reporting into four honest tiers, adds a leaf candidate finder, and decompiles 12 leaf functions to verified `matching` status.

**Tech Stack:** C++20, LLVM/Clang (`--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard`), Capstone ARMv6K disassembler, Python 3 `unittest`.

**Spec:** `docs/superpowers/specs/2026-10-21-toolchain-verification-and-matching-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Every `.cpp` translation unit under `src/` must compile cleanly to 3DS ARMv6K ELF32 object code (`--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -fno-exceptions -fno-rtti`).
- No function may be marked `matching` in `config/functions.csv` unless `tools/asm_diff.py` confirms its compiled ARMv6K `.text` bytes match `extracted/exefs/code.bin` (100% byte/instruction match).
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` immediately above its definition with the exact ledger address, size, and name.
- Strict TDD: write/update the failing test first (RED), implement, verify the test and full suite pass (GREEN), then commit.

## Review Focus

- **Freestanding ARMv6K header isolation:** compiling with `--target=armv6k-none-eabihf` on Windows must not pull in MinGW `_mingw.h` (`#error Only Win32 target is supported!`); `include/freestanding/` and `-nostdinc -nostdinc++` must isolate target headers cleanly.
- **Thumb trailing halfword in `tools/split_asm.py`:** functions in the Thumb region (`0x00100048..0x00101300`) whose last 2 bytes cannot be disassembled must emit `.short` instead of crashing `struct.unpack_from("<I")` at buffer end.
- **ELF32 symbol matching in `tools/asm_diff.py`:** must match both `extern "C"` (`func_name`) and Itanium C++ mangled (`_Z...<len><func_name>...`) symbols in `.symtab`.
- **Fake `matching` rejection in `tools/progress.py`:** marking a function `matching` whose compiled bytes differ from `code.bin` must raise `VerificationError`.
- **Progress counter backward compatibility & split tiers:** `compute_progress()` must retain `decompiled_functions`/`decompiled_bytes`/`matching_functions`/`matching_bytes` while adding `verified_functions`, `verified_bytes`, `draft_functions`, and `draft_bytes`.

---

### Task 1: Fix Broken Translation Units & Freestanding ARMv6K Build Pipeline

**Files:**
- Create: `include/freestanding/cstddef`
- Create: `include/freestanding/cstdint`
- Create: `include/freestanding/cstring`
- Create: `include/freestanding/cmath`
- Create: `include/freestanding/algorithm`
- Create: `include/freestanding/string.h`
- Create: `include/freestanding/math.h`
- Create: `tools/build_check.py`
- Create: `tests/test_build.py`
- Modify: `include/engine/asd_symbols.h`
- Modify: `include/ui/status.h`
- Modify: `src/ui/result.cpp`
- Modify: `tools/split_asm.py`
- Modify: `tests/test_tools.py`
- Modify: `CMakeLists.txt`

**Interfaces:**
- Produces:
  - `tools.build_check.find_clang() -> Path`
  - `tools.build_check.compile_tu_armv6k(src_file: Path, out_obj: Path, repo_root: Path = Path(".")) -> subprocess.CompletedProcess`
  - `tools.build_check.compile_all_armv6k(repo_root: Path = Path("."), out_dir: Path = Path("build/obj/armv6k")) -> dict` (`{"total": int, "succeeded": int, "failed": list[tuple[str, str]], "objects": dict[str, Path]}`)

- [ ] **Step 1: Write failing tests in `tests/test_build.py` and `tests/test_tools.py` (RED)**

In `tests/test_build.py`:
```python
import unittest
from pathlib import Path
from tools.build_check import compile_all_armv6k, find_clang


class TestArmv6kBuild(unittest.TestCase):
    def test_find_clang_exists(self):
        clang = find_clang()
        self.assertTrue(clang.exists(), f"Clang not found at {clang}")

    def test_all_translation_units_compile_to_armv6k(self):
        result = compile_all_armv6k(Path("."), Path("build/obj/armv6k"))
        self.assertGreaterEqual(result["total"], 68)
        self.assertEqual(
            result["failed"],
            [],
            f"Translation units failed ARMv6K compilation: {result['failed']}",
        )
        self.assertEqual(result["succeeded"], result["total"])
```

Also add a test in `tests/test_tools.py` for disassembling Thumb function `0x00100238` (20 bytes) and `0x00100b44` (32 bytes) without `struct.error` on trailing 2-byte halfwords.

- [ ] **Step 2: Run the test suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'tools.build_check'`).

- [ ] **Step 3: Fix the 10 broken TUs, Thumb disassembler edge case, and create `include/freestanding/*` + `tools/build_check.py`**

1. In `include/engine/asd_symbols.h`: add a `namespace smt4::ui` block at the bottom exposing `using ::AsdMem_Alloc; using ::AsdMem_Zero; using ::AsdTask_CreateCalc; using ::AsdTask_CreateDraw;` so all UI/battle/camp/script/shop TUs calling `ui::AsdMem_Alloc` etc. resolve cleanly.
2. In `src/ui/result.cpp`: include `"engine/asd_symbols.h"`.
3. In `include/ui/status.h`: fix `StatusWork::pad_30` array size from `0x11CC` to `0x12BC` so `offsetof(StatusWork, sub_state_ec) == 0x12EC` holds (`0x30 + 0x12BC == 0x12EC`).
4. In `tools/split_asm.py` line 166: when `not disassembled_any`, check `if pos + 4 <= size:` before `struct.unpack_from("<I", chunk, pos)`; otherwise unpack `<H` (`.short 0x{h:04x}`) and advance `pos += 2`.
5. Create `include/freestanding/{cstddef,cstdint,cstring,cmath,algorithm,string.h,math.h}` providing freestanding declarations (`size_t`, `ptrdiff_t`, `nullptr_t`, fixed-width integer types via Clang builtin `<stdint.h>`/`<stddef.h>`, `memcpy`, `memset`, `memmove`, `memcmp`, `strlen`, `strcmp`, `strncmp`, `strcpy`, `strncpy`, `sinf`, `cosf`, `sqrtf`, `fabsf`, `atan2f`, `floorf`, `ceilf`, `fmodf`, `std::min`, `std::max`, `std::clamp`, `std::swap`, `std::fill`, `std::copy`).
6. Implement `tools/build_check.py` which locates `clang++.exe` (checking `PATH` and `C:\msys64\clang64\bin\clang++.exe`), queries `clang++ -print-resource-dir` for builtin headers, and compiles each `src/**/*.cpp` with `--target=armv6k-none-eabihf -mcpu=mpcore -mfpu=vfpv2 -mfloat-abi=hard -O2 -std=c++20 -fno-exceptions -fno-rtti -ffreestanding -nostdinc -nostdinc++ -isystem include/freestanding -isystem <resource_dir>/include -Iinclude -c` into `build/obj/armv6k/<rel_stem>.o` (with mtime caching so unchanged `.o` files are reused fast unless `force=True`).

- [ ] **Step 4: Run tests to verify GREEN**

Run: `python -m unittest discover -s tests -v`
Expected: PASS (all 68 `.cpp` files compile cleanly to ARMv6K ELF32 `.o` objects).

- [ ] **Step 5: Commit**

```powershell
git add CMakeLists.txt include/freestanding include/engine/asd_symbols.h include/ui/status.h src/ui/result.cpp tools/split_asm.py tools/build_check.py tests/test_build.py tests/test_tools.py
git commit -m "feat(build): fix broken TUs and add freestanding 3DS ARMv6K build pipeline"
```

---

### Task 2: ARMv6K ELF32 Assembly Diffing & Disassembly Verification Engine

**Files:**
- Create: `tools/asm_diff.py`
- Create: `tools/verify_decomp.py`
- Create: `tests/test_asm_diff.py`
- Modify: `tools/progress.py`
- Modify: `tests/test_progress.py`
- Modify: `PROGRESS.md`
- Modify: `README.md`

**Interfaces:**
- Consumes: `tools.build_check.compile_tu_armv6k`, `tools.build_check.compile_all_armv6k`
- Produces:
  - `tools.asm_diff.extract_elf_functions(obj_path: Path) -> dict[str, tuple[bytes, set[int]]]` (maps symbol name to `(func_bytes, reloc_word_offsets)`)
  - `tools.asm_diff.compare_function(addr: int, size: int, func_name: str, src_file: Path, code_bytes: bytes, repo_root: Path = Path(".")) -> dict` (`{"addr": str, "name": str, "expected_size": int, "compiled_size": int, "exact_match": bool, "byte_match_ratio": float, "mnemonic_match_ratio": float, "diff_lines": list[str]}`)
  - `tools.verify_decomp.audit_claimed_functions(functions_csv: Path, repo_root: Path, code_path: Path | None = None) -> dict`

- [ ] **Step 1: Write failing tests in `tests/test_asm_diff.py` and `tests/test_progress.py` (RED)**

In `tests/test_asm_diff.py`:
- Test `extract_elf_functions` and `compare_function`:
  - Compile a temporary `.cpp` snippet containing `engine_func_0011b838` (`0x0011b838`, 24 B) and verify `compare_function` returns `exact_match=True`, `byte_match_ratio=1.0`, `compiled_size=24`.
  - Test that a modified/non-matching snippet for `0x0011b838` returns `exact_match=False` and `byte_match_ratio < 1.0`.
- In `tests/test_progress.py`:
  - Add `test_rejects_non_identical_function_marked_as_matching`: marking a function `matching` when its compiled ARMv6K bytes do not match `code.bin` raises `VerificationError`.
  - Verify `compute_progress()` includes `verified_functions`, `verified_bytes`, `draft_functions`, and `draft_bytes` (`verified_functions + draft_functions == decompiled_functions`).

- [ ] **Step 2: Run the test suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'tools.asm_diff'`).

- [ ] **Step 3: Implement `tools/asm_diff.py`, `tools/verify_decomp.py`, and split metrics in `tools/progress.py`**

1. In `tools/asm_diff.py`:
   - Parse 32-bit little-endian ELF `.o` files (`.text`, `.symtab`, `.strtab`, `.rel.text`). Match `func_name` against either exact symbol name `func_name` or Itanium mangled symbol containing `f"{len(func_name)}{func_name}"`.
   - Slice the symbol's bytes from `.text` (`st_value` and `st_size`).
   - Compare against `code_bytes[addr - 0x00100000 : addr - 0x00100000 + size]`:
     - `exact_match` is `True` iff `compiled_size == size` and every 4-byte word (or 2-byte Thumb halfword) matches identically (for words listed in `reloc_word_offsets`, verify the opcode/condition high byte matches).
     - Disassemble both slices with Capstone to compute `mnemonic_match_ratio` and side-by-side `diff_lines`.
2. In `tools/verify_decomp.py`:
   - Classify each claimed decompiled function:
     - `matching`: verified `exact_match == True` via `asm_diff.compare_function()`.
     - `verified`: compiles to ARMv6K `.o` symbol and has non-trivial instruction coverage (`compiled_size >= min(16, expected_size)` and `compiled_size / expected_size >= 0.15`).
     - `draft`: remaining `non_matching` functions with `< 0.15` compiled size ratio.
3. In `tools/progress.py`:
   - Enforce that any row with `status == "matching"` is verified against `asm_diff.compare_function()` (raising `VerificationError` if `exact_match` is False).
   - Add `verified_functions`, `verified_bytes`, `draft_functions`, `draft_bytes` to `compute_progress()` and render them in `PROGRESS.md` and `README.md`.
   - Run `python tools/progress.py --write` to update `PROGRESS.md` and `README.md`.

- [ ] **Step 4: Run the test suite to verify GREEN**

Run: `python -m unittest discover -s tests -v`
Expected: PASS.

- [ ] **Step 5: Commit**

```powershell
git add tools/asm_diff.py tools/verify_decomp.py tools/progress.py tests/test_asm_diff.py tests/test_progress.py PROGRESS.md README.md
git commit -m "feat(tools): add ARMv6K ELF asm_diff verifier and split progress tiers"
```

---

### Task 3: Leaf Function Candidate Finder & First 12 Byte-Matching Functions (184 Bytes)

**Files:**
- Create: `tools/find_candidates.py`
- Create: `include/engine/leaf_matching.h`
- Create: `src/engine/leaf_matching.cpp`
- Modify: `config/functions.csv`
- Modify: `tests/test_progress.py`
- Modify: `tests/test_asm_diff.py`
- Modify: `PROGRESS.md`
- Modify: `README.md`

**Functions to Decompile to 100% `matching` (12 functions, 184 bytes):**
1. `engine_func_0011b838`: `0x0011b838` (24 B, `engine`)
2. `engine_func_00121ec4`: `0x00121ec4` (20 B, `engine`)
3. `engine_func_00130dcc`: `0x00130dcc` (12 B, `engine`)
4. `engine_func_00130dd8`: `0x00130dd8` (12 B, `engine`)
5. `engine_func_001311a0`: `0x001311a0` (12 B, `engine`)
6. `battle_func_00132fb8`: `0x00132fb8` (12 B, `battle`)
7. `engine_func_0015e7c0`: `0x0015e7c0` (16 B, `engine`)
8. `ui_func_0019de0c`: `0x0019de0c` (12 B, `ui`)
9. `engine_func_0022b3cc`: `0x0022b3cc` (12 B, `engine`)
10. `engine_func_002347ac`: `0x002347ac` (12 B, `engine`)
11. `engine_func_0023abc0`: `0x0023abc0` (20 B, `engine`)
12. `engine_func_0025503c`: `0x0025503c` (20 B, `engine`)

**Interfaces:**
- Consumes: `tools.asm_diff.compare_function`, `tools.progress.compute_progress`
- Produces:
  - `tools.find_candidates.find_leaf_candidates(functions_csv: Path, code_bytes: bytes, max_size: int = 64, limit: int = 50) -> list[dict]`
  - 12 `matching` functions in `src/engine/leaf_matching.cpp`

- [ ] **Step 1: Update `tests/test_progress.py` and `tests/test_asm_diff.py` expectations (RED)**

In `tests/test_progress.py`:
```python
self.assertEqual(stats["decompiled_functions"], 395)
self.assertEqual(stats["decompiled_bytes"], 537076)
self.assertEqual(stats["matching_functions"], 12)
self.assertEqual(stats["matching_bytes"], 184)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 434)
self.assertEqual(stats["total_explored_bytes"], 785316)
```
In `tests/test_asm_diff.py`:
- Add `test_find_leaf_candidates_returns_pure_leaf_functions` testing `find_leaf_candidates`.
- Add `test_all_matching_functions_in_ledger_are_byte_identical` asserting all 12 `matching` rows in `config/functions.csv` pass `compare_function` with `exact_match=True` and `byte_match_ratio=1.0`.

- [ ] **Step 2: Run the test suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL (`383 != 395`, `0 != 12`).

- [ ] **Step 3: Implement `tools/find_candidates.py`, `include/engine/leaf_matching.h`, `src/engine/leaf_matching.cpp`, and update `config/functions.csv`**

1. Implement `tools/find_candidates.py` to scan `todo` functions in `config/functions.csv` (`size <= max_size`), disassemble each with Capstone, and return pure leaf functions (no `bl`/`blx` calls, no `svc`) sorted by size and address.
2. Implement the 12 leaf functions in `include/engine/leaf_matching.h` and `src/engine/leaf_matching.cpp` with `// DECOMP_FUNC(0xXXXXXXXX, size)` markers so each compiles with `clang++ --target=armv6k-none-eabihf -mcpu=mpcore -O2` to 100% byte-identical ARMv6K instructions.
3. Update the 12 rows in `config/functions.csv` to `status=matching` and `src_file=src/engine/leaf_matching.cpp`.
4. Run `python tools/progress.py --write` to update `PROGRESS.md` and `README.md`.

- [ ] **Step 4: Run the test suite to verify GREEN**

Run: `python -m unittest discover -s tests -v`
Expected: PASS (all tests including `test_all_matching_functions_in_ledger_are_byte_identical` and `test_all_translation_units_compile_to_armv6k` pass).

- [ ] **Step 5: Commit**

```powershell
git add tools/find_candidates.py include/engine/leaf_matching.h src/engine/leaf_matching.cpp config/functions.csv tests/test_progress.py tests/test_asm_diff.py PROGRESS.md README.md
git commit -m "feat(matching): add leaf candidate finder and decompile 12 byte-matching functions (+184 B, 100% byte match)"
```
