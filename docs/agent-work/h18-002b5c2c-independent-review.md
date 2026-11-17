# Independent review: Thumb halfword counter `0x002b5c2c`

## Recommendation

**Accept the isolated semantic evidence for review purposes; do not promote this candidate into the 20-byte production slot yet.** The typed implementation and bounded differential evidence are credible for aligned, readable, zero-terminated `uint16_t` sequences, and the observed BLX interworking is correct in Unicorn. The candidate emits 32 bytes, while the catalog span is 20 bytes (the original executable body returns at byte offset 16 and the remaining `0xffff` halfword is tail/padding). It cannot be copied into the current span as-is. No reviewed/verified placement or patch strategy is supplied.

## Frozen provenance and inspected emission

All 21 read-path hashes in the review packet matched at inspection, including candidate source, runner, tests, source wrapper, per-function/contract records, producer handoff, two reports and two object files. Both objects have SHA-256 `93489a3865ec8766dbf7c822366911c457a313f35866bb81c7074811d25ead60`; both report the same 32-byte, relocation-free Thumb body:

```text
0188002909d0811c00208a1c401c098800291146f9d100287047002000287047
```

Thumb decoding shows halfword load, zero comparison/branch, pointer/count updates, loop, `cmp r0,#0`, and `bx lr`, plus a second zero-count return path ending in another `bx lr`. There are no relocations/calls. The source uses a typed `const uint16_t*` loop and a final `cmp` inline-assembly statement to establish return NZCV. The latter is flag-setting inline asm, but is a source-level implementation choice that should remain justified by the original flag contract and compiler behavior; it is not a byte-matching requirement.

The reference bytes decode as Thumb despite the production wrapper's `.arm` assembler directive: the complete 20-byte span is `002101e0491c801c0288002afad108007047ffff`; `bx lr` is at `0x002b5c3c`, and `0xffff` at `0x002b5c3e` is tail data/padding. Fifteen aligned ARM BLX-immediate sites target the helper. The pinned reference verification maps those sites to catalog owners and finds no aligned exact-pointer references. As the producer documents, this scan cannot exclude indirect, unaligned, data-driven, relocated, or computed references.

## Differential, controls and state coverage

I inspected both producer reports; I did not recompile or independently rerun the experiment (the review task has compiler budget 0). Both reports use the same object/source identity and pinned reference SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`:

| Seed | Cases | Differential | Caller windows | Controls |
|---|---:|---|---|---|
| 17 | 133 | passed | 6/6 | 3/3 detected |
| 20261116 | 133 | passed | 6/6 | 3/3 detected |

Directed cases include empty, one-element and mixed/high-bit halfwords; seeded inputs are aligned and at most 64 nonzero elements followed by a terminator. The runner checks exact byte read footprints through the terminator, no writes, input memory, `r0` count, `r4-r11`, SP/LR, NZCV, PC, and return state (the candidate returns to ARM state). It does not compare every caller-saved GPR `r1-r3`, which AAPCS permits the callee to clobber. This is acceptable for the helper's declared ABI contract but means the report does not establish full-register identity. Its memory checks are focused on the input payload and its read/write hooks, not arbitrary address-space behavior.

All three negative controls were detected in both reports: byte stepping, counting the terminator, and an incorrect count. They exercise meaningful counterexamples for element width, termination, and result calculation. They do not address malformed/unbounded pointers, null input, unaligned access, count/pointer wrap, or out-of-range faults.

## Caller composition and integration blockers

The static inventory contains all 15 aligned direct ARM BLX immediate sites found by the runner. Two representative real caller sequences are executed for counts 0, 1 and 2:

- `0x002e0e0c` in `engine_func_002e0dd0`: BLX return followed by `lsl r3,r0,#1` (`count * 2`), stop at `0x002e0e14`.
- `0x002a8868` in `ui_func_002a882c`: caller computes `(count + 1) * 2` and stores a byte length, stop at `0x002a887c`.

These confirm that two real ARM callers can enter the candidate in Thumb state and resume in ARM state with the expected count-derived length. They are short post-call windows; they do not execute full callers, all 15 uses, or downstream helpers. The caller comparison checks stop/PC, relevant output (`r3` or length slot), NZCV and ARM state, but not every register or all memory outside the specific output. Caller evidence is therefore **partial**, not broad caller equivalence.

The 32-byte candidate is 12 bytes larger than the 20-byte catalog span (14 bytes larger than the 18-byte executable original body). Direct in-place replacement is infeasible without overwriting adjacent code/data. A viable integration would need a separately verified executable location and an entry transfer that preserves the incoming LR and Thumb state. Options to investigate include a nearby Thumb branch veneer to the out-of-line body or a linker-supported Thumb helper/trampoline; a 16-bit Thumb branch has a limited reach, while a 32-bit Thumb-2 branch/veneer needs instruction-set and relocation verification in this build. There is no evidence here that a suitable cave exists, that it is mapped by the target loader, or that the patch/build tooling can preserve the Thumb function-pointer bit. Do not assume the free two-byte tail can hold anything beyond padding.

## Decision and required next step

The recovered contract is strongly supported for its stated aligned ordinary-memory domain, including actual BLX-to-Thumb entry and ARM continuation. Keep the 32-byte candidate as an isolated experiment and retain the truthful `matching` ledger label only for the unchanged original bytes. Promotion is blocked on a reviewed integration-placement plan that provides executable storage for all 32 bytes, preserves Thumb interworking at every call path, and runs the patched original caller windows through that placement. The next owner should check code layout/loader mapping and build support for a veneer or out-of-line helper, then rerun offline caller composition with the actual patched entry. Full runtime is not evidenced or required by this review.
