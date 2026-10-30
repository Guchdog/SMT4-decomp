# Independent review: `0x002B1FC0` scale-track candidate

## Verdict

Bounded acceptance for the isolated candidate is supported: I found no semantic
mismatch in the pinned body versus the readable candidate on inspected control
flow, and the frozen final differential report records 22/22 passing synthetic
fixtures plus a detected mutation control. This is partial offline ARM
differential evidence, not general equivalence, H1 caller validation, or runtime
acceptance. Do not promote it as an integrated/runtime result on this review
alone.

## Frozen identity and independent inspection

All 14 input hashes declared in
`build/agent-work/H1-semantic/h1-preview-scale-track-review/overnight-20261025-scale-review/task.json`
matched at review time. Pinned `code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; the
decoded entry is 444 bytes, `[0x002B1FC0,0x002B217C)`, body SHA-256
`9d9948ecc56a1a6dd32012eacce76ce8cffdf3902632f8efc85245d9dd1f5811`.
`split_asm.py --addr 0x002B1FC0` confirms the four return sites at
`0x002B2024`, `0x002B2114`, `0x002B2120`, and `0x002B2178`; no call instruction
occurs in this body. The helper retains input `r0` as its return value, saves
and restores `r4/r5`, and uses no stack locals or callee-saved VFP registers.

The candidate source SHA-256 is
`5226b8680178fac814a515a4bb9440aadbec37edcd156b3ec1278dd381fc30e7`. The
final report SHA-256 is
`8bd37631f19937f4db3f94d7628a8439cfcaa13cef1d0f94e7b83aa3f9402afd`; its
linked candidate text SHA-256 is
`42d7d45e94fa150c7d7ffb45b29a4430775b201ca992fd4be062b2d09e344735` and ELF
SHA-256 is `e84264a1c45652733efeac91aa1009181ca33e72d73ccd7e9d9015a6e09b92c8`.
The frozen runner and focused test hashes are respectively
`9c70fad47e5a606ff3e2a7d8816d94495166b141b8626bdc3a35b13404a3436f` and
`8349628e88f174225953f09d4b13f476787b2dff19b22d2189e0f9f862a4e977`.

## Pinned behavior cross-check

- `0x002B1FC4..0x002B1FD8` implements the early `object+0x87` and null
  `object+0x58` gates. The candidate returns without stores in each case.
- `0x002B1FDC..0x002B1FF4` sign-extends row index `+0x5C` and progress `+0x5E`,
  computes `table + 12*index`, loads unsigned duration at row `+8`, and uses
  signed `GT` against progress. Candidate address arithmetic and comparison
  preserve these widths/signs for the tested ARM target.
- At `0x002B2124..0x002B2178`, direction byte `+0x60` chooses `row[0]-row[1]`
  or `row[1]-row[0]`. The original performs single-precision subtract, unsigned
  duration-to-float conversion, divide, add to object float `+0x20`, and stores
  halfword `progress+1`. Candidate keeps that operation sequence and halfword
  truncation.
- `0x002B1FF8..0x002B2020` selects the endpoint using row mode `+0x0A` and
  signed direction `+0x60`; it clears progress. Candidate's direction/row-mode
  endpoint selection agrees on both branches.
- `0x002B2028..0x002B204C` first stores the opposite endpoint and then checks
  sequence-enabled byte `+0x84` and pointer `+0x78`. The sequence current entry
  address is `base+0x0C+28*signed_index`; current marker `-1` completes. The
  incremented index is sign-extended and stored as a halfword before the next
  marker is read from `base+28*index+0x0C`. Next `-1` and `-3` complete; `-2`
  resets the index and loads row/direction from the first entry at `+0x0C/+0x10`.
  Ordinary entries sign-extend the low row halfword and signed direction byte
  `+0x10`. Candidate follows these offsets and ordering, resets progress, clears
  `+0x8A` only on selected-row transition, and stores the new endpoint. Disabled
  or null sequence sets completion after the earlier endpoint store.

The scale helper's static caller is confirmed by pinned disassembly of
`0x002BF9F0`: at `0x002BFC2C` it moves `r4` to `r0` and calls `0x002B1FC0` at
`0x002BFC30`. That establishes the direct argument convention only. The caller
continues into sibling helpers `0x002B1DFC` and `0x002B1C8C`; the H1 object
binding, those sibling interactions, lifecycle, and runtime scene are not
validated here.

## Differential and controls

The final frozen run-04 report has `compile_exit=0`, `passed=true`, and 22/22
cases. Each case returns to the LR sentinel and agrees in `r0`, `r4-r11`, SP,
`d8-d15`, FPSCR, caller-owned stack, and the full synthetic data mapping. The
matrix covers both early gates, both endpoint modes/directions, both interpolation
directions, negative progress, zero duration and divide-by-zero status,
maximum-duration/progress halfword wrap, a negative row index with valid
preceding storage, sequence-disabled/null/current-end/next-`-1`/next-`-3`/next-`-2`
and ordinary transition branches, and extreme finite float inputs. The reported
FPSCR values match for the divide-by-zero, inexact, and overflow cases; this is
consistent with the pinned VFP sequence and does not imply every float payload or
FPSCR mode was explored.

The negative control removes the candidate's selected-transition `+0x8A` clear.
It is detected by the memory projection: original object byte `+0x8A` is `0`,
mutant byte is `1`. The control therefore exercises a real observable store.

The implementer handoff records superseded runs accurately: run-01 failed on
VFP execution because FPEXC was not enabled; run-02 passed but had two sequence
fixtures that did not enter sequence logic; run-03 corrected those fixtures and
passed 21/21; run-04 adds a signed-progress/max-duration case and passes 22/22.
I inspected the archived reports and handoff descriptions. The run-02 report
does not serialize original fixture table/sequence bytes, so the exact invalid
fixture inputs cannot be independently reconstructed from that report alone;
the correction is supported by the handoff's explicit account and the final
runner's corrected `row_mode=0` sequence fixtures.

## Limits and next action

The matrix uses synthetic, valid, non-overlapping memory. It does not prove
unchecked invalid-pointer/index behavior, all halfword-wrap domains, aliasing,
concurrent mutation, MMIO, or captured live track state. There is no candidate
caller differential, integrated replacement, or Azahar/game-runtime run. The
candidate and records correctly label evidence partial and preserve the exact
ledger classification. Next action: coordinator may consider this isolated
candidate for a separate integration decision after reviewing dependencies and
defining the H1 scenario; this review does not authorize promotion or runtime
claims.

## Review commands

Read-only commands used (all exited 0):

- `python tools/split_asm.py --addr 0x002B1FC0`
- `python tools/split_asm.py --addr 0x002BF9F0`
- A Python read-only SHA-256 audit of every path in the review packet's
  `input_sha256` map (14 inputs; no mismatches).
- A Python read-only summary of run-01 through run-04 reports and comparison of
  their recorded case outcomes.

No compilation, test execution, emulator, or runtime control was performed.
