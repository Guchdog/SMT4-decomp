# Independent production review: `UiConfig_FillPair` (`0x0027EDF8`)

## Recommendation

Accept the production helper for the reviewed bounded contract: replicate the
low byte of a `u32` into two consecutive ARM words at a destination covering
eight writable bytes of ordinary RAM, including each destination alignment
modulo four. The production body, slot placement, patch artifact, and dedicated
4,096-case differential are internally consistent. The State-9/10 caller run
also records the expected `work+0x1C`, `0xFFFFFFFF` invocation in both original
and patched paths.

This is bounded helper and offline caller-composition evidence. It does not
establish allocator success/alignment for every caller, arbitrary address or
MMIO behavior, H2 interactive behavior, persistence, or Azahar runtime
equivalence.

## Contract and production body

Pinned original `code.bin` SHA-256 is
`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The
function record and caller audit describe a 24-byte ARM function at
`0x0027EDF8`: mask the second argument to its low byte, replicate that byte
through all four byte lanes, then store the word to `[r0]` and `[r0,#4]`; there
are no source reads, calls, or global writes. The caller audit found no caller
consumption of the return value or condition flags.

The production C++ in `src/engine/leaf_matching.cpp` takes `u8*` and `u32`, uses
defined unsigned shifts/ORs for replication, and emits the two `str` operations
in inline ARM assembly with a memory clobber. This avoids imposing a C++ `u32*`
alignment requirement while retaining the original access width. The manifest's
body is 24 bytes and decodes to `uxtb`, two `orr`, two `str`, and `bx lr`; the
only instruction-level difference from the original in this body is the
equivalent `uxtb` for `and #0xff`. The compiled object has no relocations.

The patch manifest places the body in the existing 24-byte slot at
`0x0027EDF8`. Its original-image interior-reference scan covers 10,967
ledgered spans for direct ARM B/BL/BLX targets and aligned absolute words across
`code.bin`; it reports no references into the function interior. This supports
the fixed-slot replacement within that scan. It does not cover computed or
relative branches, unaligned pointer data, Thumb code, or unledgered/runtime
references.

## Caller alignment and extent

The static caller audit identifies seven direct ARM BL sites. Six pass offsets
divisible by four assuming a word-aligned object base; `camp_func_001d14fc`
passes `g_ConfigWork+0x76`, which is 2 modulo 4 on that assumption. The other
H2 callers pass `TitleConfigWork+0x1C`. The declared `TitleConfigWork` size is
`0x158`, so the helper's eight-byte span at `+0x1C` is in bounds if allocation
succeeds and returns the expected object. The audit correctly leaves allocator
success and alignment as assumptions; dynamic objects rooted at
`0x00439C88+0x20` also lack a proven allocation extent/lifecycle.

The dedicated production differential covers destination offsets 0, 1, 2,
and 3, so it includes the observed halfword-aligned case. It validates this
ARM-emulated ordinary-memory contract, not fault behavior, MMIO semantics, or
all callers' object lifetimes. Thus the `+0x76` concern about a misaligned C++
word pointer is addressed by the current implementation, while the caller
preconditions remain conditional.

## Artifact and differential verification

Packet frozen-input hashes all matched before review. I independently recomputed
the relevant artifact/report hashes and checked the replacement bytes against
the manifest:

| Artifact | SHA-256 | Review check |
|---|---|---|
| Production source `src/engine/leaf_matching.cpp` | `b5e511d0bae599ac38a13b6df68918444c00aece51ebcb760e0817897c18adf8` | Matches manifest and differential report |
| Production object | `b59d0fa7d71b58be50b08ef10a9c0061816c5b37c3f23c5318a39313869bd3e3` | Matches manifest and differential report |
| Mapper-extended base image | `97b6c2ab9ea7f15904bbee3ad42115599bd3529220dbfba818a77bbbcfbe321c` | Matches manifest's base; length 3,633,152 bytes |
| Incremental IPS | `5b0a75a1526aec8db88b0f02cf0f9eef98e657a51a5b2bb5e1993932b9d5a4c2` | Matches manifest; 37 bytes |
| Patched combined image | `5e9aa08b449985f012e24400c45b4b037e4a0d5d069723b6cfa7ccf83300d8fa` | Matches manifest and final/caller reports; same length as base |
| Helper differential report | `208a4df775ec281a9467538acab60c6f6c6b99685c075f9376368d4d63a98d6b` | 4,096/4,096; negative control detected |
| Combined-image validation report | `8cc19997ae04b54791fb383c711859fbfa5d7a27288b2c30c15ba7b711263f7a` | Passed all listed offline suites |
| State-9/10 caller report | `6369612ea7d681cd43f99d107ad1f7db60c2ae69a522185efe4450a457d35cb4` | 3/3; wrong callback control detected |

The patch image has the manifest's exact six-instruction body at the slot and
matches the mapper-extended base everywhere outside those 24 bytes. Three byte
values differ between base and patched image, consistent with only changing
the first instruction's encoding while retaining the other instructions.

The helper report exhausts all 256 low-byte values for each of four upper-bit
patterns at each destination offset: `4 * 4 * 256 = 4096` cases. It reports
equal original/candidate write sets, no first counterexample, and detects a
wrong-mask candidate (`value & 0xFFFF`) as a data-memory difference. That
control exercises the low-byte-only contract and is sensitive to high-byte
leakage. The source operation itself makes the general low-byte semantics
clear; the finite upper-pattern set is not an enumeration of every possible
upper 24-bit value.

The combined final-image report passes Calc 16 sequences/54 ticks, Draw 46,
Secondary 34, initializer 10, and ready gate 4, with per-family negative
controls. The exact-image caller report passes three State-9/10 phases and
detects a wrong primary Calc callback address. Its trace records the FillPair
call at `0x0027EDF8` with `r0=0x0200201C`, `r1=0xFFFFFFFF` on both sides. The
combined image includes earlier H2 replacements, so those suite totals are
composition evidence for that full offline image, not an isolated FillPair
measure.

## Acceptance limits and follow-up

The caller run uses explicit HLE boundaries for allocator/factories, task
lookups, sprite/resource/cursor setup, touch registration, environment/model
services, and other helpers. It observes registration/readiness/reset flow;
it does not schedule or execute Calc, Draw, or Secondary, and it does not
validate user input, rendering, edit/cancel/confirm behavior, save persistence,
restart, or a real game runtime. The pair-fill helper's isolated report is the
direct behavioral evidence for its byte stores; the combined/caller results
provide placement and exercised initializer context under their harness.

The existing `docs/function-records/0x0027edf8.md` still describes the earlier
experimental candidate and isolated-only status, rather than this production
implementation and review. Update the record and ledger through the assigned
integration/closure owner; the record should retain the supported target-memory
domain and caller allocator limits. Do not present this report or the offline
image as whole-H2 or runtime acceptance.

No build, test, emulator, or UI action was performed for this independent
review. No implementation, record, ledger, milestone, or board files were
changed.
