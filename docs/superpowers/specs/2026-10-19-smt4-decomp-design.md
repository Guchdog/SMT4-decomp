# Shin Megami Tensei IV (`CTR-P-AMXE`) Decompilation Project Design

**Date:** 2026-10-19  
**Target Title:** *Shin Megami Tensei IV* (US, v0.1.0, Title ID `00040000000E5C00`, Product Code `CTR-P-AMXE`, Internal Name `sdds4`)  
**Repository:** `https://github.com/Guchdog/SMT4-decomp`

---

## 1. Intent and Why

The goal of this project is to decompile *Shin Megami Tensei IV* (Nintendo 3DS) from the user's local CIA copy into clean, human-readable, modifiable C/C++ source code and structured data/script formats.

The long-term purpose of having readable source code is:
1. **Custom Modifications:** Being able to freely understand and modify game systems—specifically reworking the dual-screen HUD, menus, and UI layouts.
2. **Cross-Platform Porting:** Serving as the foundation for native PC and Android ports where 3DS-specific dual-screen layouts and hardware services (`nn::`, PICA200 GPU, DSP audio) are replaced by portable equivalents.
3. **Reliable, Measurable Progress:** Proceeding methodically with a byte-accurate function ledger and progress tracker so that at any point we know exactly how many functions and bytes of `code.bin` (and which subsystems, such as HUD/UI vs. battle vs. SDK) are decompiled and what remains untouched.

---

## 2. Target Binary & ROM Profile

Inspection of the user's local CIA (`00040000000E5C00 Shin Megami Tensei IV (CTR-P-AMXE) (v0.1.0) (U).piratelegit.cia`) and `aes_keys.txt` established the following exact technical layout:

- **Encryption:**
  - Outer CIA content layer encrypted with the Title Key (derived via `slot0x3DKeyX` + `common0` normal key and Ticket IV `00040000000e5c00...`).
  - Inner NCCH container uses standard `slot0x2CKeyX` (`SecCrypto = 0x00`, no 7.x KeyX or SeedDB required).
- **Monolithic Native Executable (`ExeFS/.code`):**
  - Unlike many 3DS titles, *Shin Megami Tensei IV* uses **no `.cro` dynamic modules**. 100% of the native ARMv6K code is statically linked inside `ExeFS/.code`.
  - Compressed size in ExeFS: `0x20AC90` bytes (2,091.1 KB), using standard 3DS Backward LZ77 (BLZ).
  - Uncompressed memory segments (defined in `ExHeader`):
    - **`.text` (Code):** `0x00100000` – `0x003FE624` (`0x2FE624` bytes / 3,065.5 KB)
    - **`.rodata` (Read-Only Data / Strings / VTables):** `0x003FF000` – `0x0042AB78` (`0x2BB78` bytes / 174.9 KB)
    - **`.data` (Initialized Data):** `0x0042B000` – `0x00476644` (`0x4B644` bytes / 301.6 KB)
    - **`.bss` (Uninitialized Globals):** `0x00477000`, size `0x797F0` bytes (486.0 KB)
- **RomFS Assets & Game Logic (`1,786.49 MB`, `20,126` files across 33 top-level directories):**
  - Top-level directories: `addon`, `banner_icon`, `battle`, `bible`, `camp`, `cec`, `cec_icon`, `character`, `clear_save`, `effect`, `effect_editor`, `event`, `font`, `item`, `map`, `mikado`, `moflex`, `name`, `npc_room`, `ones_room`, `player`, `player_arms`, `quest_center`, `saveLoadER`, `saveLoadUI`, `shop`, `snd`, `status`, `terminal`, `test`, `tex`, `title`, `unite`, `zzz_dummy`.
  - High-level game and UI flow relies heavily on `1,437` `.bf` (Atlus FlowScript bytecode) files, `1,170` `.mbm` message tables, `386` `.tbb` / `48` `.tbl` / `111` `.ttd` binary tables (including UI layout tables like `SaveLoadUITable.tbb`), and `3,066` `.stex` / `447` `.tga` textures.

---

## 3. Goals, Non-Goals, and Anti-Goals

### Goals
- **Automated Local Extraction Pipeline (`tools/extract.py`):** Decrypt and unpack the local `.cia` using `aes_keys.txt`, decompress `ExeFS/.code` (BLZ) into `extracted/exefs/code.bin` + `exheader.bin`, and support full or selective extraction of `RomFS` files (`extracted/romfs/...`).
- **Complete Function Catalog (`config/functions.csv` & `config/symbols.csv`):** Identify every function in the `0x2FE624`-byte `.text` segment of `code.bin`, recording its exact start address, end address, size in bytes, status (`todo`, `wip`, `non_matching`, `matching`), subsystem category (`ui`, `battle`, `camp`, `script_vm`, `render`, `engine`, `nn_sdk`, `crt`, `unknown`), symbol name, and target C++ file path.
- **Disassembly & Source Workspace (`asm/` and `src/`):**
  - Split undecompiled functions and data references into readable ARMv6K assembly files (generated locally into `build/asm/` or `asm/` from the user's `code.bin` so the repo stays clean and fast).
  - Organize decompiled C/C++ source code under `src/` (`src/ui/`, `src/battle/`, `src/camp/`, `src/script/`, `src/engine/`, `src/nn/`, etc.) with shared headers in `include/`.
- **Reliable Progress Tracking (`tools/progress.py` & `PROGRESS.md`):**
  - Compute exact decompilation metrics by **function count** and **byte size** across the entire `.text` segment (`3,139,108` bytes) and per subsystem category.
  - Generate both terminal output and a committed `PROGRESS.md` dashboard (plus JSON stats) so progress is clearly visible on GitHub (`https://github.com/Guchdog/SMT4-decomp`) after every push.
- **HUD/UI Discovery & Inspection Tooling (`tools/inspect_romfs.py` / symbol tagging):**
  - Automatically cross-reference string literals in `.rodata` (such as paths to `/battle/`, `/camp/`, `/status/`, `/mikado/`, `.tbb`, `.stex`, `.bf`) against `.text` code references so HUD, UI, and FlowScript VM functions in `code.bin` are immediately labeled in the function ledger rather than buried among 10,000 unnamed `sub_XXXXXX` functions.

### Non-Goals (For Initial Foundation)
- Decompiling all ~10,000 functions immediately before committing the workspace infrastructure.
- Shipping proprietary ROM binaries, `.cia` files, `code.bin`, `aes_keys.txt`, or copyrighted RomFS assets in the public GitHub repository.

### Anti-Goals (What Would Make This a Failure)
- **Blind/Unverified Progress Claims:** Counting stubbed or empty C++ files as "decompiled" without tracking exact byte ranges and function statuses in the ledger.
- **Leaking Copyrighted Assets or Keys to Git:** Committing `.cia`, `code.bin`, `aes_keys.txt`, or extracted RomFS data to `Guchdog/SMT4-decomp`.
- **Opaque Monolithic Dumps:** Producing a single giant unreadable 100 MB disassembly text file instead of a structured, categorized function database and modular `src/` hierarchy focused on modifiable systems like the HUD.

---

## 4. Constraints & Environment

- **Host OS:** Windows (`powershell`).
- **Available Tooling:** Python 3.14.7 with `PyCryptodome` (`Crypto`) and `capstone` (ARM/Thumb disassembly engine) already installed.
- **Legal / Git Safety:** `.gitignore` must strictly block `*.cia`, `*.3ds`, `*.bin`, `aes_keys.txt`, `extracted/`, `romfs/`, `exefs/`, and `build/`. A verification step (`tools/verify_cia.py` or `tools/extract.py --check`) validates the user's local `code.bin` SHA-256 hash so any contributor with the same game copy can reproduce the workspace.

---

## 5. Architecture & Decisions Made

### 5.1 Repository Layout (Committed to GitHub)
```text
SMT4decomp/
├── .gitignore
├── README.md                  # Project overview, setup instructions, and live progress summary
├── PROGRESS.md                # Auto-generated detailed progress report by subsystem & bytes
├── CMakeLists.txt             # C++ build configuration for decompiled source code
├── config/
│   ├── game_info.json         # Title ID, segment addresses/sizes, expected SHA-256 hashes
│   ├── functions.csv          # Master ledger of every function in .text (addr, size, status, category, name, file)
│   └── symbols.csv            # Data/rodata/bss symbols and string-inferred labels
├── docs/
│   ├── architecture.md        # SMT4 engine, HUD/UI tables, and FlowScript (.bf) overview
│   └── superpowers/specs/     # Design and implementation plans
├── include/
│   ├── types.h                # Standard fixed-width types, 3DS structs, macros
│   ├── ui/                    # HUD, camp, status, and layout headers
│   ├── script/                # FlowScript (.bf) & message (.mbm) VM structures
│   └── engine/                # Core engine and math/resource structures
├── src/
│   ├── crt/                   # Entrypoint (__start) and runtime initialization
│   ├── ui/                    # Decompiled HUD, menu, and layout C++ code
│   ├── battle/                # Battle system and battle HUD C++ code
│   ├── camp/                  # Camp menu / Demonicas UI C++ code
│   ├── script/                # FlowScript (.bf) interpreter and native command handlers
│   └── engine/                # Core file loader, memory, and rendering wrappers
└── tools/
    ├── extract.py             # Decrypts CIA, decompresses BLZ .code, extracts ExeFS & RomFS
    ├── analyze_code.py        # Scans code.bin with Capstone, finds all functions & xrefs, tags subsystems via .rodata strings
    ├── split_asm.py           # Disassembles any function or range into readable ARM/Thumb .s files with rodata/symbol comments
    ├── progress.py            # Computes byte/function progress and updates PROGRESS.md & README.md
    └── inspect_assets.py      # Inspects RomFS UI tables (.tbb/.tbl) and FlowScript (.bf) headers for HUD modding
```

### 5.2 Local-Only Extracted Data (`extracted/`, git-ignored)
- `extracted/exheader.bin` (`0x800` bytes)
- `extracted/exefs/code.bin` (`0x3751E0` bytes / 3,625,440 bytes uncompressed `.text` + `.rodata` + `.data`)
- `extracted/exefs/banner.bin`, `icon.bin`, `logo.bin`
- `extracted/romfs_index.json` (complete manifest of all 20,126 RomFS files with offsets and sizes, plus on-demand or full extraction to `extracted/romfs/`)

### 5.3 Function Discovery & Automatic Subsystem Categorization (`tools/analyze_code.py`)
1. **Function Boundary Analysis:**
   - Uses Capstone (ARMv6K + Thumb/Thumb-2 + VFPv2) starting from the entrypoint (`0x00100000`), exception vectors, `.rodata` / `.data` function pointer tables (vtables and script native callback tables), `BL` / `BLX` call targets, and standard ARM function prologues (`PUSH {..., lr}` / `STMFD sp!, {..., lr}`).
   - Partitions the entire `.text` section (`0x00100000` – `0x003FE624`) so every function has a well-defined start address and byte size.
2. **Automatic String & Xref Labeling:**
   - Scans `.rodata` (`0x003FF000` – `0x0042AB78`) and `.data` (`0x0042B000` – `0x00476644`) for ASCII/Shift-JIS/UTF-16 strings (file paths like `battle/`, `camp/`, `status/`, `saveLoadUI/`, `mikado/`, debug strings, class/RTTI names, SDK strings).
   - Resolves literal pool loads (`LDR rX, [pc, #imm]`) in `.text` to map strings to functions, automatically tagging functions that belong to `ui`, `battle`, `camp`, `script_vm`, `shop`, `unite`, `nn_sdk`, etc.

### 5.4 Progress Tracking & Verification (`tools/progress.py`)
- Reads `config/functions.csv` and verifies that every function marked `matching`, `non_matching`, or `wip` actually has a corresponding implementation in `src/`.
- Calculates:
  - **Total `.text` Bytes Decompiled:** `decompiled_bytes / 3,139,108` (with separate counts for `matching` vs `non_matching`/`wip` C++ implementations).
  - **Total Functions Decompiled:** `decompiled_funcs / total_funcs`.
  - **Subsystem Progress Table:** Progress broken down by `ui` (HUD/menus), `battle`, `camp`, `script_vm`, `engine`, `nn_sdk`, `crt`, and `unknown`.
- Writes `PROGRESS.md` and updates the progress badges/summary in `README.md` ready to commit and push to `https://github.com/Guchdog/SMT4-decomp`.

---

## 6. Builder Calls (Decided by Designer)

The following technical choices are set as sensible defaults so implementation can proceed smoothly:
- **Language & Standard:** C++20 for decompiled source (`src/`, `include/`) with `CMakeLists.txt`, and Python 3 for all build/extraction/analysis scripts (`tools/`).
- **Selective vs. Full RomFS Extraction:** `tools/extract.py` will extract `exheader.bin`, `code.bin`, and `romfs_index.json` by default (plus UI/HUD/script directories on demand or `--all` for all 1.78 GB) so setup completes in seconds without wasting disk I/O unless full asset extraction is requested.
- **Initial Decompiled Seed:** As part of the initial setup, we will decompile the entrypoint (`__start` / CRT startup) and initial HUD/UI-related functions discovered during analysis so the C++ build, `PROGRESS.md`, and verification workflow are demonstrated end-to-end on the first push to GitHub.
