# Semantic Reconstruction Night Shift

> Historical plan, superseded by the semantic-first objective in [AGENTS.md](../../../AGENTS.md) and [functional status](../../functional-status.md). Its requirement to keep every reconstruction byte-identical is no longer the acceptance policy.

**Starting point:** commit `133b379` completed byte-exact coverage of the full
`0x00100000..0x003FE624` text segment: 10,959 functions plus 8 explicitly
labeled raw spans, totaling 3,139,108 bytes. The baseline test suite passes all
52 tests, including the private `code.bin` audit and the ARM/CMake build.

**Goal:** replace exact assembly and `.incbin` wrappers with readable C++ in
small, independently verifiable batches while preserving 100% byte equality.
This is semantic reconstruction work; do not treat existing wrapper coverage as
readable source coverage.

## Non-negotiable guardrails

- Work only on the current branch, `codex/add-400-exact-matches`.
- Never modify, regenerate, or commit private inputs under `extracted/`, CIA
  files, keys, build outputs, or caches.
- Preserve every ledger address, size, symbol name, category, and source-file
  mapping unless disassembly proves the ledger itself is wrong.
- Preserve `matching` status only when `tools/asm_diff.py` reports an exact
  match. If readable C++ cannot match after a bounded attempt, revert that
  function and continue; do not downgrade the project-wide exact baseline.
- Do not replace callable code with new raw bytes, inline assembly, `.incbin`,
  or compiler-specific byte directives. The point of each accepted edit is
  readable C++.
- Do not reinterpret literal pools or raw spans as callable functions without
  control-flow evidence.
- Keep each commit narrow: ideally 10-30 related leaf functions or one coherent
  subsystem family. The tree must be clean and tests green after every commit.
- Do not push, open a PR, rewrite history, or alter earlier commits.

## Repeatable work loop

1. Refresh the queue:

   ```powershell
   python tools/find_candidates.py --status matching --asm-backed-only --max-size 64 --limit 100
   ```

2. Choose a coherent set, preferably from one source file or subsystem. Inspect
   each function with `python tools/split_asm.py --addr <address>` and inspect
   nearby callers, literals, existing structs, and sibling semantic functions.
3. Replace only the selected wrapper bodies with typed C++ and the minimum
   declarations needed. Preserve the exact `DECOMP_FUNC` marker and symbol.
4. Rebuild the touched translation unit and compare every edited function:

   ```powershell
   python tools/build_check.py --tu <repo-relative-source-file>
   python tools/asm_diff.py --addr <address>
   ```

5. Run the focused tests, then the full suite before committing:

   ```powershell
   python -m unittest tests.test_find_candidates -v
   python -m unittest discover -s tests -v
   git diff --check
   ```

6. Commit the verified batch with an imperative message such as
   `Replace 24 exact leaf wrappers with readable C++`. Record addresses and any
   unresolved type/signature questions in the commit body or a short note in
   this file.
7. Repeat until time expires. End with a clean worktree. If the final batch is
   incomplete, revert only that batch rather than leaving failing code.

## First queue

These call-free entries were confirmed by the candidate finder and are suitable
for the first pass. They are ordered roughly by difficulty.

| Address | Size | Suggested C++ behavior |
|---|---:|---|
| `0x002e07a8` | 4 | Empty `eventView_DrawUp` body (`bx lr`) |
| `0x0023a350` | 8 | No-op preserving/returning `r0` |
| `0x0036a29c` | 8 | No-op preserving/returning `r0` |
| `0x00381464` | 8 | No-op preserving/returning `r0` |
| `0x00121d70` | 12 | Signed byte load from object offset `0x330` |
| `0x00131414` | 12 | Store `r1`/`r2` to offsets `+4` and `+8` |
| `0x00138288` | 12 | FPSCR configuration; defer if portable C++ cannot express it exactly |
| `0x00144ea0` | 12 | Float load from object offset `0x49C` |
| `0x0014ec5c` | 12 | Nullable pointer load from offset `0x1C` |
| `0x00158784` | 12 | Store `r1`/`r2` to offsets `+0x84` and `+0x88` |
| `0x0017f5c0` | 12 | Store zero to `*r0` |
| `0x0018f554` | 12 | Return `p ? p + 8 : nullptr` |
| `0x0023347c` | 12 | Store `r1`/`r2` to offsets `+0x40` and `+0x44` |
| `0x002345f0` | 12 | Load low byte of halfword at `+0x48` |
| `0x002345fc` | 12 | Load low byte of halfword at `+0x4A` |
| `0x00292e88` | 12 | Store `r1`/`r2` to offsets `+0x40` and `+0x44` |
| `0x002c7084` | 12 | Copy four contiguous floats (16 bytes) |
| `0x002dd080` | 12 | Copy four contiguous floats (16 bytes) |
| `0x002f3450` | 12 | Copy four contiguous floats (16 bytes) |
| `0x002f98e0` | 12 | Copy four contiguous floats (16 bytes) |

After this list, continue with 16- and 20-byte call-free wrappers from the same
queue command. Favor repeated instruction shapes: field getters/setters,
constant returns, paired-word stores, null-aware pointer adjustments, small
counter updates, and fixed-size copies. These are high-throughput and easy to
audit. Defer FPU status writes, unusual ABI thunks, tail calls, literal-pool
owners, and functions with external branches until the ordinary leaf queue is
exhausted.

## Definition of a successful night

- At least one committed batch replaces wrappers with readable C++.
- Every edited function remains byte-exact according to `asm_diff.py`.
- The full 52-test baseline still passes; additional tests may increase that
  count.
- `python tools/verify_decomp.py` reports no matching or compilation failures.
- `git diff --check` passes and the worktree is clean.
- The final report lists commits, converted addresses/count, deferred cases,
  and the exact command output for the final validation.
