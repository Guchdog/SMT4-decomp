# 23% Decompilation Milestone: Unknown Runtime Blocks and Camp/CRT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 8 previously-unmapped engine/CRT/camp functions totaling 31,448 bytes, raising total architecture explored from **690,968 bytes (22.0116%)** to **722,416 bytes (23.0135%)** and authentically decompiled code from **442,728 bytes (14.1036%)** to **474,176 bytes (15.1054%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/runtime_blocks.h` / `src/engine/runtime_blocks.cpp`: four large runtime blocks (16,484 B).
- `include/engine/runtime_blocks2.h` / `src/engine/runtime_blocks2.cpp`: four more runtime blocks (14,964 B).
- `config/functions.csv`: flips the 8 rows from `todo` to `non_matching`.
- `tests/test_progress.py`: pins exact cumulative counters after each task.

**Tech Stack:** C++20, ARMv6K disassembly (`tools/split_asm.py` + Capstone), Python 3.12 progress verifier, MSVC BuildTools x86 compile checks.

**Spec:** `docs/superpowers/specs/2026-10-19-smt4-decomp-design.md`

## Global Constraints

- Target binary: `extracted/exefs/code.bin` (`0x377000` bytes, SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`).
- Never invent struct layouts or behavior: every field offset, branch, call target, and constant must be traceable to the function's disassembly. Pre-indexed loads (`LDR rX,[rY,#imm]!`) must use the effective post-writeback offset.
- Every decompiled function must carry `// DECOMP_FUNC(0xXXXXXXXX, size)` immediately above its definition with the exact ledger address/size/name.
- Do not mark a function `non_matching` unless its body implements the observed control flow; comment-only placeholders remain `stub`.
- One declaration per binary address: shared helpers go in `include/engine/asd_symbols.h` or the module header; no duplicate names/signatures/linkage.
- Every assigned global must have exactly one definition with observed initial values (`.data` initializers included).
- Strict TDD: update `tests/test_progress.py` first (RED), implement, then `python tools/progress.py --write` and the full suite (GREEN), then commit. Compile the touched TUs with MSVC BuildTools x86.
- Preserve style: fixed-width types from `include/types.h`, four-space indentation, opaque structs with `static_assert(offsetof(...))`.

## Review Focus

- **Compile correctness and call ABI:** every helper call must match the actual register/stack argument shape.
- **Pre-indexed writeback and strides:** verify every 4/8/0x10/0x18/0x1C/0x2C/0x8C stride.
- **`.data` initializers and producers:** globals need observed values and documented producers.
- **Large block bodies:** do not collapse loops/dispatch into summaries.
- **Progress claims:** exact cumulative counters after each task.

---

### Task 1: Runtime blocks A (4 functions, 16,484 bytes)

**Files:**
- Create: `include/engine/runtime_blocks.h`
- Create: `src/engine/runtime_blocks.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `func_003b11a8`: `0x003b11a8` (4,548 B)
- `crt_func_00101308`: `0x00101308` (4,144 B)
- `func_00142bf0`: `0x00142bf0` (4,008 B)
- `camp_func_002831f0`: `0x002831f0` (3,784 B)

- [x] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 363)
self.assertEqual(stats["decompiled_bytes"], 459212)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 402)
self.assertEqual(stats["total_explored_bytes"], 707452)
```

- [x] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `363 != 359`.

- [x] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr <address>`. Recover roles from literals/call graphs. Keep exact ledger names (including `crt_func_*` and `camp_func_*`), document recovered roles, and preserve all calls/branches/stores.

- [x] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/runtime_blocks.cpp`. Run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 363 / 459,212 B, 39 / 248,240 B, 402 / 707,452 B; all tests PASS.

- [x] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile four runtime blocks (+16,484 B, 22.54% explored)"
```

---

### Task 2: Runtime blocks B (4 functions, 14,964 bytes)

**Files:**
- Create: `include/engine/runtime_blocks2.h`
- Create: `src/engine/runtime_blocks2.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `func_00160e90`: `0x00160e90` (3,776 B)
- `func_00164c08`: `0x00164c08` (3,776 B)
- `func_00168980`: `0x00168980` (3,776 B)
- `func_002f9f54`: `0x002f9f54` (3,636 B)

- [x] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 367)
self.assertEqual(stats["decompiled_bytes"], 474176)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 406)
self.assertEqual(stats["total_explored_bytes"], 722416)
```

- [x] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `367 != 363`.

- [x] **Step 3: Disassemble and implement**

The three `0x0016xxxx` entries are near-identical 3,776-byte blocks; recover the shared core and per-block differences. Preserve the full control flow.

- [x] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/runtime_blocks2.cpp`; expected 367 / 474,176 B, 406 / 722,416 B (23.0135%); all tests PASS.

- [x] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile four runtime blocks B (+14,964 B, 23.0% milestone reached at 23.0135%)"
```
