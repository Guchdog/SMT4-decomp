# 20% Decompilation Milestone: Engine Runtime and Script VM Extras Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Authentically decompile 8 previously-unmapped engine/script runtime functions totaling 32,248 bytes, raising total architecture explored from **596,804 bytes (19.0119%)** to **629,052 bytes (20.0386%)** and authentically decompiled code from **348,564 bytes (11.1039%)** to **380,812 bytes (12.1304%)** in Shin Megami Tensei IV (`CTR-P-AMXE`).

**Architecture:**
- `include/engine/asd_runtime.h` / `src/engine/asd_runtime.cpp`: four large engine runtime routines (16,488 B).
- `include/script/script_vm_extras.h` / `src/script/script_vm_extras.cpp`: four large script VM routines (15,760 B).
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

- **Compile correctness and call ABI:** every helper call must match the callee's actual register/stack argument shape.
- **Pre-indexed writeback and stride arithmetic:** use the effective post-writeback base and verify every 4/8/0x10/0x18/0x1C/0x2C stride.
- **`.data` initializers and singleton producers:** globals read by the new bodies must carry their binary initial values; null-initialized pointers need a documented producer.
- **Script VM state:** opcode/state dispatch, flag-bank accesses, and task/process ownership must preserve observed ordering.
- **Summary stubs:** a 4,672-byte `engine_func_001aba94` or 4,384-byte `script_vm_func_00276cac` reduced to a few statements is a defect.
- **Progress claims:** exact cumulative counters after each task; regenerate only via `python tools/progress.py --write`.

---

### Task 1: Engine runtime routines (4 functions, 16,488 bytes)

**Files:**
- Create: `include/engine/asd_runtime.h`
- Create: `src/engine/asd_runtime.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `engine_func_001aba94`: `0x001aba94` (4,672 B)
- `engine_func_002e4b10`: `0x002e4b10` (4,116 B)
- `engine_func_0018844c`: `0x0018844c` (4,016 B)
- `engine_func_00304164`: `0x00304164` (3,684 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 343)
self.assertEqual(stats["decompiled_bytes"], 365052)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 382)
self.assertEqual(stats["total_explored_bytes"], 613292)
```

- [ ] **Step 2: Run the suite to verify it fails**

Run: `python -m unittest discover -s tests -v`
Expected: FAIL with `343 != 339`.

- [ ] **Step 3: Disassemble and implement**

Use `python tools/split_asm.py --addr <address>`. Recover each routine's role from its literals/call graph (`engine_func_001aba94` references `map/mr01/mr01_%02d.bam` and `map/mr02/mr02_%02d.bam`). Keep the ledger names and document the recovered role. Preserve all observed calls, branches, and state stores.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/engine/asd_runtime.cpp`. Run:

```powershell
python tools/progress.py --write
python -m unittest discover -s tests -v
```

Expected: 343 / 365,052 B, 39 / 248,240 B, 382 / 613,292 B; all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(engine): decompile four large engine runtime routines (+16,488 B, 19.54% explored)"
```

---

### Task 2: Script VM extras (4 functions, 15,760 bytes)

**Files:**
- Create: `include/script/script_vm_extras.h`
- Create: `src/script/script_vm_extras.cpp`
- Modify: `tests/test_progress.py`
- Modify: `config/functions.csv`

**Functions:**
- `script_vm_func_00276cac`: `0x00276cac` (4,384 B)
- `script_vm_func_00399f28`: `0x00399f28` (3,928 B)
- `script_vm_func_0039d8b8`: `0x0039d8b8` (3,792 B)
- `script_vm_func_002c8c90`: `0x002c8c90` (3,656 B)

- [ ] **Step 1: Update progress test expectations (RED)**

```python
self.assertEqual(stats["decompiled_functions"], 347)
self.assertEqual(stats["decompiled_bytes"], 380812)
self.assertEqual(stats["stub_functions"], 39)
self.assertEqual(stats["stub_bytes"], 248240)
self.assertEqual(stats["total_explored_functions"], 386)
self.assertEqual(stats["total_explored_bytes"], 629052)
```

- [ ] **Step 2: Run the suite to verify it fails**

Expected: FAIL with `347 != 343`.

- [ ] **Step 3: Disassemble and implement**

Recover each routine's role from its opcode tables/literals. Preserve opcode/state dispatch, flag-bank accesses, and task/process ownership ordering. Keep the ledger names and document the recovered role.

- [ ] **Step 4: Update the ledger and verify GREEN**

Set `status=non_matching`, `src_file=src/script/script_vm_extras.cpp`; expected 347 / 380,812 B, 386 / 629,052 B (20.0386%); all tests PASS.

- [ ] **Step 5: Commit**

```powershell
git commit -m "feat(script): decompile four large script VM routines (+15,760 B, 20.0% milestone reached at 20.0386%)"
```
