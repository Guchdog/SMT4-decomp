# Independent review: preview-helper plus editable row setter

## Verdict

**Bounded composition evidence is supported, with explicit projection limits.**
The frozen run-v4 artifacts establish that the original side executes pinned
helper `0x002BF9F0` and continues into pinned setter `0x002BDAC0`; the candidate
side executes the helper C++ and reaches the compiled setter C++ through the
private adapter. Neither setter entry is handled by a setter stub hook. All
eight report cases pass, and the omitted-`+0x50` store mutation is detected.
This remains partial evidence under four stubbed callees and synthetic
non-aliasing state; it does not validate live H1 behavior or authorize runtime
claims.

## Frozen identities

All 15 packet input hashes matched during review. Pinned image SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
helper extent `[0x002BF9F0,0x002BFC88)` is 664 bytes with SHA-256
`9b4783c2ccc69b30fc99ef28b04fe5f5abbe1762f99a13551facc5cab7b8217e`; the
setter extent `[0x002BDAC0,0x002BDB2C)` is 108 bytes with SHA-256
`e9c60d31db041884aa6fe44db47bcabc849bf08464d1465a68cad24c4b1f152a`.

Source hashes are helper C++
`64c3964b0abae2c0ff6e51d1e9ef5961c8e8d0769e177c528a878d4b094b3282`, setter
C++ `653f143c22f46a30ac2f5fe183f5d305927fca5f4959ef69d9a2f38f477377fc`,
runner `7df3f1f59bb4c942e29909e640c5a328d6a4f06011a8c7e2685b593bbfc0f0db`,
and tests `1012207c7a603913a638209f1cf740a09d1fb6aca18dffe7679581d6e731eadd`.
Final run-v4 report SHA-256 is
`65068c65af75bbd64bdce364697ae472d2fa3154522e5db83cb4e5b89cc5bab2`; linked
candidate ELF SHA-256 is
`5a28811a7ed502c10b07ffcd3222eeea6084c305a315dbc518ad8afd9f5efd5e`, text
SHA-256 `c66500944836565196639976eb7a40456f62d8236c9d61cb7f7e1e1034c7739b`.
The generated adapter source hash is
`9b8bb005586196202240bb09ad283843b984cd306e51cd922111cb54f4d3ef17`.

## Setter execution path audit

Pinned disassembly of the helper shows both setter call sites:

- Restart path at `0x002BFB60..0x002BFB78`: loads the first sequence word and
  signed frame byte, places object/animation/frame in `r0/r1/r2`, and calls
  `0x002BDAC0` at `0x002BFB78`.
- Ordinary next-entry path at `0x002BFB3C..0x002BFB48`: sign-extends the next
  animation word and frame byte, places the same three arguments, and calls
  `0x002BDAC0` at `0x002BFB48`.

On the original side, `Machine._hook` checks `pc == SETTER` only to record the
arguments, then returns without changing PC or LR. `SETTER` is absent from
`ORIGINAL_STUBS`, so Unicorn executes the pinned setter body. The report records
one original call at `0x2bdac0` for each path.

On the candidate side, the helper's `camp_func_002bdac0` symbol is a separate,
`noinline` adapter that calls `h1_animation_row_setter_candidate`. The hook
records the adapter entry but does not redirect execution. The linked adapter
disassembles to an unconditional branch from `0x01000570` to setter C++ at
`0x010004AC`. The setter symbol is not in `STUBS` or `stub_symbols`; the only
candidate stubs are interpolation and the three tail helpers. The report
records matching adapter arguments for restart `(object,2,0)` and ordinary-next
`(object,2,1)` calls. This independently corroborates the original/candidate
composition seam, not the actual live caller.

The candidate adapter preserves the setter ABI's three arguments in
`r0/r1/r2`: object pointer, signed animation row index, signed mode/frame value.
The candidate helper extracts these values with `SXTH` and `LDRSB`-equivalent
reads in its C++ before calling the adapter. The setter C++ is compiled as a
separate object with the candidate helper and adapter; the final ELF has no
undefined symbols.

## Fixture and mutation audit

The frozen final report has `passed=true`, eight cases, and `first_mismatch=null`:

1. Null row-table pointer skips setter.
2. Endpoint with sequence disabled skips setter.
3. Next sequence word `-2` restarts through setter call site one.
4. Ordinary next sequence entry advances through setter call site two.
5. Interpolation direction zero invokes both interpolation stubs.
6. Interpolation direction one invokes both interpolation stubs.
7. Nonzero row mode bypasses enabled sequence handling.
8. Enabled but null sequence marks completion without setter.

Both setter paths receive the expected object and arguments. The comparison
checks final full 16-KiB synthetic data mapping, return `r0`, ordered named stub
calls and arguments, setter call count/arguments, `r4-r11`, SP, `d8-d15`, and the
caller-owned stack; it also checks original/candidate callee-saved invariance.
The omission control recompiles a private mutation that removes the setter's
`+0x50` row-index store. In the ordinary-next case the original memory contains
halfword `2` at `+0x50`, the mutant retains `0`, and the full-data comparison
detects the error.

The run history has an identifiable superseded report in `results/`: its
8-case run fails first on `valid null table returns without setter` with a
named-stub trace mismatch. In the saved traces, names, arguments, and returns
match while PCs differ by design (pinned addresses versus candidate linked
addresses); the current runner normalizes those PCs before comparing. `results-v2/`
contains a mutation source but no report, so its outcome cannot be independently
reconstructed from saved artifacts. `results-v3/` is an 8/8 passing report;
`results-v4/` is the final packet-pinned run and also passes 8/8 plus the
mutation control. The final handoff identifies v4 as the successful command.

## Limits and next action

Four direct callees remain stubs: `0x002C615C` returns zero for interpolation;
`0x002B1FC0`, `0x002B1DFC`, and `0x002B1C8C` are no-ops. Their real side effects,
ABIs beyond the arguments shown, and transitive behavior are unresolved. Cases
use valid, non-overlapping synthetic object/row/sequence storage and do not
establish H1 object construction or scene lifecycle.

The projection captures FPSCR but does not assert original/candidate FPSCR
equality. These fixtures execute no VFP instructions in the helper or setter,
and interpolation is a zero-return stub, so this is a recorded but unchecked
projection field. It also omits caller-saved scratch registers (`r1-r3`, `r12`),
CPSR flags, memory access order/multiplicity, and transient state. The runner
does compare final full mapped data and relevant call traces, but these limits
bound the conclusion. No caller-level H1 scenario, emulator/game runtime, or
asset lifecycle was tested. Next action: keep this as a partial synthetic
composition result and recover the remaining helper contracts before any
integration or runtime conclusion.

## Review commands

Read-only commands used:

- An initial typo `python tools.split_asm.py ...` exited 2 (incorrect module
  path); the corrected disassembly commands below completed successfully.
- `python tools/split_asm.py --addr 0x002BDAC0` (exit 0).
- `python tools/split_asm.py --addr 0x002BF9F0` (exit 0).
- `llvm-objdump.exe -d .../results-v4/candidate-build/composed_candidate.elf`
  filtered for the adapter, setter, and `bl` instructions (exit 0).
- Python SHA-256 audits of the 15 frozen packet inputs and composition ELF,
  linked text, adapter and final report (exit 0 for the declared inputs and
  final artifacts).
- Python read-only summary of the saved results/results-v2/results-v3/results-v4
  attempts (exit 0).
- `python tools/agent_workflow.py check-handoff --packet <review-task.json>
  --handoff <review-handoff.json>` (exit 0 after handoff creation).

No compilation, test execution, emulator, or game-runtime control was performed.
