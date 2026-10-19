# Shin Megami Tensei IV Decompilation Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the complete extraction, ARMv6K function discovery, HUD/UI subsystem tagging, C++20 decompilation workspace, and byte-accurate GitHub progress tracking pipeline for *Shin Megami Tensei IV* (`CTR-P-AMXE`).

**Architecture:** A Python 3 extraction and static analysis pipeline decrypts the local CIA using `aes_keys.txt`, decompresses the BLZ-compressed `ExeFS/.code` binary (`3,625,440` bytes across `.text`, `.rodata`, `.data`), catalogs every function in the `3,139,108`-byte `.text` segment into `config/functions.csv` with `.rodata` string cross-referencing to label HUD/UI and gameplay subsystems, and tracks decompiled C++ functions in `src/` with byte-accurate verification in `PROGRESS.md` and `README.md`.

**Tech Stack:** Python 3.14 (`pycryptodome`, `capstone`, `unittest`), C++20, CMake, Git/GitHub.

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints

- **Target Title:** *Shin Megami Tensei IV* (US, v0.1.0, Title ID `00040000000E5C00`, Product Code `CTR-P-AMXE`, Internal Name `sdds4`).
- **Memory Map (from ExHeader):**
  - `.text`: `0x00100000` – `0x003FE624` (`0x2FE624` bytes / `3,139,108` bytes; page-aligned size `0x2FF000`)
  - `.rodata`: `0x003FF000` – `0x0042AB78` (`0x2BB78` bytes / `179,064` bytes; page-aligned size `0x2C000`)
  - `.data`: `0x0042B000` – `0x00476644` (`0x4B644` bytes / `308,804` bytes)
  - `.bss`: `0x00477000`, size `0x797F0` bytes (`497,648` bytes)
- **Git Safety:** Never stage or commit `*.cia`, `aes_keys.txt`, `extracted/`, `code.bin`, or any proprietary binary assets to `https://github.com/Guchdog/SMT4-decomp`.
- **Host Environment:** Windows PowerShell; Python 3.14 with `Crypto` (`pycryptodome`) and `capstone` already installed.

## Review Focus

1. **BLZ Decompression Padding / Header Offsets:** 3DS `.code` Backward LZ77 stores `compressed_size`, `header_size`, and `additional_size` at the end of the compressed buffer, and `.text`/`.rodata`/`.data` in `code.bin` are concatenated on `0x1000` page boundaries (`0x2FF000 + 0x2C000 + 0x4B644 = 0x376644` bytes). If BLZ decompression miscalculates tail padding or page alignment, `.rodata` and `.data` addresses will be shifted and every string xref will break.
2. **AES-CBC / AES-CTR Streaming Alignment on 1.78 GB RomFS:** Reading arbitrary RomFS files must correctly align both the outer CIA TitleKey AES-CBC block IV (previous 16-byte ciphertext block) and the inner NCCH AES-CTR counter (`partition_id_rev + section_type(3) + (romfs_offset >> 4)`). Misaligned reads corrupt extracted `.tbb` and `.bf` files.
3. **Contiguous `.text` Byte Coverage in `config/functions.csv`:** If function boundary discovery leaves gaps or overlapping ranges in `0x00100000..0x003FE624`, the sum of function sizes will not equal `0x2FE624` (`3,139,108` bytes), making byte-progress percentages inaccurate.
4. **False-Positive Progress Inflation in `tools/progress.py`:** Marking a function as `non_matching` or `matching` in `config/functions.csv` when its `src_file` does not exist or does not contain the function symbol must fail verification rather than counting toward progress.
5. **Literal Pool Data Inside `.text` Misidentified as Instructions:** ARMv6K compilers embed 32-bit constant pools between functions in `.text`. Treating literal pool words as function entrypoints creates bogus functions; `analyze_code.py` must track literal pool targets (`[pc, #imm]`) and exclude them from function prologues.

---

### Task 1: CIA Decryption, BLZ `.code` Decompression & RomFS Extraction (`tools/extract.py`)

**Files:**
- Create: `config/game_info.json`
- Create: `tools/extract.py`
- Create: `tests/test_extract.py`

**Interfaces:**
- Produces:
  - `config/game_info.json` containing exact Title ID, segment addresses/sizes, and SHA-256 of decompressed `code.bin`.
  - `tools/extract.py` with functions:
    - `load_aes_keys(path: Path) -> dict[str, bytes]`
    - `decompress_blz(data: bytes) -> bytes`
    - `CIAExtractor(cia_path: Path, keys_path: Path)` with methods `extract_exefs(out_dir: Path) -> dict`, `build_romfs_index(out_dir: Path) -> list[dict]`, `extract_romfs_files(out_dir: Path, filter_exts: list[str] | None = None, filter_dirs: list[str] | None = None) -> int`

- [ ] **Step 1: Write the failing unit tests in `tests/test_extract.py`**

```python
import unittest
from pathlib import Path
from tools.extract import decompress_blz, load_aes_keys, CIAExtractor

class TestExtract(unittest.TestCase):
    def test_load_aes_keys(self):
        keys = load_aes_keys(Path("aes_keys.txt"))
        self.assertIn("slot0x2CKeyX", keys)
        self.assertIn("slot0x3DKeyX", keys)
        self.assertIn("common0", keys)
        self.assertEqual(len(keys["generator"]), 16)

    def test_extract_exefs_and_blz_page_alignment(self):
        cia = next(Path(".").glob("*.cia"))
        ext = CIAExtractor(cia, Path("aes_keys.txt"))
        info = ext.extract_exefs(Path("extracted"))
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        # Page-aligned .text (0x2FF000) + page-aligned .rodata (0x2C000) + .data (0x4B644) = 0x376644
        self.assertEqual(len(code_bytes), 0x376644)
        self.assertEqual(info["app_title"].strip(), "sdds4")

    def test_romfs_unaligned_file_extraction(self):
        cia = next(Path(".").glob("*.cia"))
        ext = CIAExtractor(cia, Path("aes_keys.txt"))
        index = ext.build_romfs_index(Path("extracted"))
        self.assertEqual(len(index), 20126)
        count = ext.extract_romfs_files(Path("extracted/romfs"), filter_dirs=["/saveLoadUI"])
        self.assertEqual(count, 3)
        tbb = Path("extracted/romfs/saveLoadUI/SaveLoadUITable.tbb").read_bytes()
        self.assertEqual(tbb[:4], b"TBBL")
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests/test_extract.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools'`

- [ ] **Step 3: Implement `config/game_info.json` and `tools/extract.py`**

Implement `tools/extract.py` with:
- 128-bit 3DS key scrambler (`rol128((rol128(kx, 2) ^ ky) + gen, 87)`).
- Streaming AES-CBC (TitleKey) + AES-CTR (`slot0x2CKeyX`) reader that handles arbitrary RomFS file offsets by seeking to the preceding 16-byte AES-CBC block boundary and computing the exact 16-byte AES-CTR block counter (`partition_id_rev + section_type + (section_offset >> 4)`).
- Fast C-accelerated or memoryview-sliced 3DS BLZ backward LZ77 decompressor (`decompress_blz`) verifying decompressed length `0x376644`.
- CLI flags: `--check` (verifies `code.bin` SHA-256 against `config/game_info.json`), `--romfs-dirs`, `--romfs-exts`, and `--all`.

- [ ] **Step 4: Run extraction and unit tests to verify they pass**

Run: `python -m unittest tests/test_extract.py -v`
Expected: PASS (all 3 tests pass, `extracted/exefs/code.bin` is `3,630,660` bytes / `0x376644` bytes, and `SaveLoadUITable.tbb` starts with `TBBL`).

- [ ] **Step 5: Commit and push**

```powershell
git add config/game_info.json tools/extract.py tests/test_extract.py
git commit -m "feat(extract): add CIA decryptor, BLZ .code decompressor, and RomFS extractor"
git push
```

---

### Task 2: ARMv6K Function Discovery, Literal Pool Xrefs & Subsystem Categorizer (`tools/analyze_code.py`)

**Files:**
- Create: `tools/analyze_code.py`
- Create: `tests/test_analyze_code.py`
- Create: `config/functions.csv`
- Create: `config/symbols.csv`

**Interfaces:**
- Consumes: `extracted/exefs/code.bin` (`0x376644` bytes) and `config/game_info.json`
- Produces:
  - `config/functions.csv` with columns: `address,size,status,category,name,src_file`
  - `config/symbols.csv` with columns: `address,section,type,name,string_preview`
  - `analyze_binary(code_path: Path, game_info_path: Path) -> tuple[list[dict], list[dict]]`

- [ ] **Step 1: Write the failing unit tests in `tests/test_analyze_code.py`**

```python
import csv
import unittest
from pathlib import Path
from tools.analyze_code import analyze_binary, vaddr_to_offset

class TestAnalyzeCode(unittest.TestCase):
    def test_vaddr_to_offset_mapping(self):
        self.assertEqual(vaddr_to_offset(0x00100000), 0x0)
        self.assertEqual(vaddr_to_offset(0x003FF000), 0x2FF000)
        self.assertEqual(vaddr_to_offset(0x0042B000), 0x32B000)

    def test_contiguous_text_coverage_and_literal_pool_exclusion(self):
        funcs, symbols = analyze_binary(Path("extracted/exefs/code.bin"), Path("config/game_info.json"))
        self.assertGreater(len(funcs), 5000)
        # First function is entrypoint __start at 0x00100000
        self.assertEqual(funcs[0]["address"], "0x00100000")
        self.assertEqual(funcs[0]["name"], "__start")
        # Sum of all function sizes must equal exact .text size (0x2FE624 = 3,139,108 bytes) with zero overlaps/gaps
        total_size = sum(int(f["size"]) for f in funcs)
        self.assertEqual(total_size, 0x2FE624)
        # Ensure subsystems like ui, battle, camp, script_vm are discovered via .rodata string xrefs
        categories = {f["category"] for f in funcs}
        for expected_cat in ("crt", "ui", "battle", "camp", "script_vm", "nn_sdk"):
            self.assertIn(expected_cat, categories)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests/test_analyze_code.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.analyze_code'`

- [ ] **Step 3: Implement `tools/analyze_code.py` and generate `config/functions.csv` & `config/symbols.csv`**

Implement `tools/analyze_code.py`:
- Map virtual addresses using page-aligned ExHeader layout: `.text` at file offset `0x0` (`0x00100000..0x003FE624`), `.rodata` at `0x2FF000` (`0x003FF000..0x0042AB78`), `.data` at `0x32B000` (`0x0042B000..0x00476644`).
- Scan `.rodata` and `.data` for ASCII strings and pointer tables into `.text`.
- Scan `.text` 32-bit words to collect:
  1. All `LDR rX, [pc, #imm]` literal pool target addresses (mark those addresses as data words inside `.text` so they are never treated as function starts).
  2. All `BL` / `BLX` branch targets (`0xEBxxxxxx` / `0xFAxxxxxx`) within `0x00100000..0x003FE624`.
  3. All ARM function prologues (`PUSH {..., lr}` / `STMFD sp!, {..., lr}`, `SUB sp, sp, #imm` preceded by return/`BX lr`/literal pool).
- Partition `0x00100000..0x003FE624` into contiguous non-overlapping function ranges whose sizes sum to `0x2FE624` (`3,139,108` bytes).
- Resolve literal pool loads in each function to `.rodata` strings and propagate subsystem labels (`ui` for HUD/saveLoadUI/status/terminal/title/tbb strings, `battle` for battle strings, `camp` for camp strings, `script_vm` for `.bf`/FlowScript strings, `shop`, `unite`, `nn_sdk` for `nn::` SDK strings, `crt` for startup).
- Write `config/functions.csv` and `config/symbols.csv`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_analyze_code.py -v`
Expected: PASS

- [ ] **Step 5: Commit and push**

```powershell
git add tools/analyze_code.py tests/test_analyze_code.py config/functions.csv config/symbols.csv
git commit -m "feat(analysis): catalog all code.bin functions and tag HUD/UI/gameplay subsystems"
git push
```

---

### Task 3: Annotated Disassembler (`tools/split_asm.py`) & HUD/Script Asset Inspector (`tools/inspect_assets.py`)

**Files:**
- Create: `tools/split_asm.py`
- Create: `tools/inspect_assets.py`
- Create: `tests/test_tools.py`

**Interfaces:**
- Consumes: `extracted/exefs/code.bin`, `config/functions.csv`, `config/symbols.csv`, and extracted `.tbb` / `.bf` files
- Produces:
  - `disassemble_function(code_bytes: bytes, addr: int, size: int, symbols: dict[int, str], func_names: dict[int, str]) -> str` in `tools/split_asm.py`
  - `parse_tbb_header(data: bytes) -> dict` and `parse_bf_header(data: bytes) -> dict` in `tools/inspect_assets.py`

- [ ] **Step 1: Write the failing unit tests in `tests/test_tools.py`**

```python
import unittest
from pathlib import Path
from tools.split_asm import disassemble_function
from tools.inspect_assets import parse_tbb_header, parse_bf_header

class TestDecompTools(unittest.TestCase):
    def test_disassemble_entrypoint(self):
        code_bytes = Path("extracted/exefs/code.bin").read_bytes()
        asm_text = disassemble_function(code_bytes, 0x00100000, 0x48, {}, {0x00100000: "__start"})
        self.assertIn(".global __start", asm_text)
        self.assertIn("0x00100000:", asm_text)

    def test_parse_tbb_and_bf_headers(self):
        tbb_path = Path("extracted/romfs/saveLoadUI/SaveLoadUITable.tbb")
        tbb_info = parse_tbb_header(tbb_path.read_bytes())
        self.assertEqual(tbb_info["magic"], "TBBL")
        self.assertGreater(tbb_info["entry_count"], 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests/test_tools.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.split_asm'`

- [ ] **Step 3: Implement `tools/split_asm.py` and `tools/inspect_assets.py`**

- In `tools/split_asm.py`: Use Capstone (`CS_ARCH_ARM`, `CS_MODE_ARM`) to disassemble any function by address, name, or subsystem category (`--category ui`), automatically switches between instructions and embedded literal pool `.word` entries, and annotates `BL` targets and `[pc, #imm]` literal pool loads with symbol names and `.rodata` string values.
- In `tools/inspect_assets.py`: Parse SMT4 `.tbb` (`TBBL` binary tables used for UI/HUD/shop layouts) and Atlus `.bf` (`FLW0` FlowScript bytecode headers, section tables, procedure names, and message strings) so HUD layouts and script entrypoints can be inspected cleanly.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m unittest tests/test_tools.py -v`
Expected: PASS

- [ ] **Step 5: Commit and push**

```powershell
git add tools/split_asm.py tools/inspect_assets.py tests/test_tools.py
git commit -m "feat(tools): add annotated ARMv6K disassembler and TBB/BF HUD asset inspector"
git push
```

---

### Task 4: C++20 Source Tree, Initial Decompiled Functions & Architecture Docs

**Files:**
- Create: `CMakeLists.txt`
- Create: `include/types.h`
- Create: `include/ui/tbb_table.h`
- Create: `include/script/flowscript.h`
- Create: `src/crt/start.cpp`
- Create: `src/ui/tbb_loader.cpp`
- Create: `docs/architecture.md`
- Modify: `config/functions.csv`

**Interfaces:**
- Consumes: Disassembled output from `tools/split_asm.py` for `__start` (`0x00100000`) and initial `ui` / `crt` functions.
- Produces: Compilable C++20 source files in `src/` with exact `// DECOMP_FUNC: 0xXXXXXXXX` markers verified by `tools/progress.py`.

- [ ] **Step 1: Inspect the assembly of `__start` (`0x00100000`) and initial `ui`/table functions using `tools/split_asm.py`**

Run: `python tools/split_asm.py --addr 0x00100000` and `python tools/split_asm.py --category ui --limit 5`
Expected: Annotated ARMv6K assembly output showing instruction flow, called functions, and referenced `.rodata` strings/constants.

- [ ] **Step 2: Create `CMakeLists.txt`, `include/types.h`, `include/ui/tbb_table.h`, `include/script/flowscript.h`, `src/crt/start.cpp`, `src/ui/tbb_loader.cpp`, and `docs/architecture.md`**

- `include/types.h`: Fixed-width types (`u8`, `u16`, `u32`, `u64`, `s8`, `s16`, `s32`, `s64`, `f32`, `f64`, `Result`), `DECOMP_FUNC(addr)` annotation macro.
- `src/crt/start.cpp` & `src/ui/tbb_loader.cpp`: Clean C++20 decompilations of the actual instructions from `code.bin` for startup/CRT initialization and UI table (`TBBL`) parsing/lookup functions, annotated with their exact virtual addresses.
- Update the corresponding rows in `config/functions.csv` with `status=non_matching` (or `wip`), `name`, and `src_file`.

- [ ] **Step 3: Verify C++ syntax and structure**

Run a syntax/structure check on all `.cpp` and `.h` files.

- [ ] **Step 4: Commit and push**

```powershell
git add CMakeLists.txt include/ src/ docs/architecture.md config/functions.csv
git commit -m "feat(src): add C++20 project structure, headers, and initial decompiled CRT/UI functions"
git push
```

---

### Task 5: Byte-Accurate Progress Tracker & GitHub Dashboard (`tools/progress.py`, `PROGRESS.md`, `README.md`)

**Files:**
- Create: `tools/progress.py`
- Create: `tests/test_progress.py`
- Create: `PROGRESS.md`
- Create: `README.md`

**Interfaces:**
- Consumes: `config/functions.csv`, `config/game_info.json`, and `src/**/*.cpp`
- Produces:
  - `compute_progress(functions_csv: Path, repo_root: Path) -> dict`
  - `PROGRESS.md` and `README.md` with live progress badges, subsystem breakdowns, and HUD/decompilation workflow documentation.

- [ ] **Step 1: Write the failing unit tests in `tests/test_progress.py`**

```python
import tempfile
import unittest
from pathlib import Path
from tools.progress import compute_progress, VerificationError

class TestProgress(unittest.TestCase):
    def test_rejects_claimed_function_without_src_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            csv_path = root / "functions.csv"
            csv_path.write_text(
                "address,size,status,category,name,src_file\n"
                "0x00100000,72,non_matching,crt,__start,src/crt/missing.cpp\n",
                encoding="utf-8",
            )
            with self.assertRaises(VerificationError):
                compute_progress(csv_path, root)

    def test_real_repo_progress_matches_text_size(self):
        stats = compute_progress(Path("config/functions.csv"), Path("."))
        self.assertEqual(stats["total_bytes"], 0x2FE624)
        self.assertGreater(stats["decompiled_functions"], 0)
        self.assertGreater(stats["decompiled_bytes"], 0)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m unittest tests/test_progress.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'tools.progress'`

- [ ] **Step 3: Implement `tools/progress.py` and generate `PROGRESS.md` and `README.md`**

- Verify that every row in `config/functions.csv` with `status in ("matching", "non_matching", "wip")` specifies an existing `src_file` under `src/` that contains the function's address marker (`0x00100000`) and function name; raise `VerificationError` if any claimed function is missing.
- Output overall byte progress (`decompiled_bytes / 3,139,108`), function count progress, and a Markdown table broken down by subsystem (`ui`, `battle`, `camp`, `script_vm`, `shop`, `unite`, `engine`, `nn_sdk`, `crt`, `unknown`).
- Generate `PROGRESS.md` and `README.md`.

- [ ] **Step 4: Run full test suite to verify everything passes**

Run: `python -m unittest discover -s tests -v`
Expected: PASS (all unit tests across `test_extract.py`, `test_analyze_code.py`, `test_tools.py`, and `test_progress.py` pass).

- [ ] **Step 5: Commit and push to GitHub**

```powershell
git add tools/progress.py tests/test_progress.py PROGRESS.md README.md
git commit -m "feat(progress): add byte-accurate progress verifier and generate PROGRESS.md & README.md"
git push
```
