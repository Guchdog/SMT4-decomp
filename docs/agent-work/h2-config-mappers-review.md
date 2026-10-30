# Independent review: H2 config-byte mappers

## Review result

**Recommendation:** accept the three isolated C++ mappings as semantically supported over the observed caller domain, and allow them into a trial integration batch. This recommendation is limited to `0x002CAB70`, `0x0021F39C`, and `0x002E0AF4`. It does not approve the `titleConfig` initializer or close H2. Keep the exact ledger classifications describing the current original wrappers; any promoted non-identical C++ replacements need the project's supported non-matching classification and these semantic records.

I independently checked the pinned image identity, table bytes, original instruction sequences, initializer call sites, candidate source, runner, tests, function records, and both final reports. I did not edit implementation files or run a build/emulator.

## Contract and boundary review

The current `code.bin` matches the configured US v0.1.0 SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Direct byte reads at the original literal targets confirm:

| Function | Table address | Ordered thresholds | Caller input / stored output |
|---|---:|---|---|
| `0x002CAB70` | `0x004077EB` | `0, 10, 20, 25, 30, 35, 40, 45, 50, 70, 90` | `LDRB g_ConfigBytes[0]` / `TitleConfigWork+0x28` |
| `0x0021F39C` | `0x004077F6` | `0, 10, 20, 30, 40, 50, 60, 70, 80, 100, 120` | `LDRB g_ConfigBytes[1]` / `TitleConfigWork+0x2C` |
| `0x002E0AF4` | `0x00407801` | `0, 10, 20, 30, 40, 50, 60, 70, 80, 100, 120` | `LDRB g_ConfigBytes[2]` / `TitleConfigWork+0x30` |

Each original starts with the table's first byte at index zero. It returns the first index whose threshold is greater than or equal to `r0`; when the input exceeds all eleven thresholds it returns zero. The otherwise surprising zero fallback above the maximum is faithfully implemented. The title initializer's three `LDRB` instructions establish the complete valid domain as zero-extended bytes `0..255`; the mapper runner exhausts this entire domain. Equality at every threshold and both sides of every boundary are therefore covered, including zero and the above-maximum fallback.

The original ARM bodies load a literal table address, read bytes, compare, and use `r1-r3`; they do not write memory or touch stack/callee-saved/VFP callee-saved state. The initializer immediately stores each returned `r0` and does not consume mapper condition flags. Candidate signatures use a 32-bit unsigned parameter/return, matching ARM's `r0` ABI, and the compiled branches preserve the tested callee-saved state. The candidate's direct comparisons remove immutable-table reads; this is a valid effect difference for this ordinary read-only ROM data. Both reports show all 11 original table bytes read across the exhaustive domain, no candidate table reads, and empty data/stack write sets.

## Differential evidence audit

- Both reports identify the same pinned image hash, candidate source hash `adac4cf4eaea7ac2945ac4b4e7164d582c416e4123da2c0f170aada17af4852d`, object hash `43cade5047336d41f37767f45690107666339d3f0f579c0922e404f12bd13dcb`, and Clang 23.1.3 ARMv6K compile command with exit 0. Candidate functions are 132 bytes each versus 92 original bytes; no byte identity is claimed.
- Seed 7 and seed 20261024 each report 512 comparisons per mapper: every byte value plus 256 seeded cases. All six function results pass, report no first counterexample, and identify caller/runtime evidence as not run.
- The A-map negative control changes the 10 threshold to 11. At input 11, the pinned original returns 2 and the faulty candidate returns 1; the expected mismatch is detected. This is a meaningful off-by-one boundary control. It directly probes the unusual first interval after zero; the all-byte positive comparison separately covers B and C thresholds.
- The focused unit tests check the reference table function at all byte values, each threshold and following value, fallback, and the wrong-map distinction. They are useful support checks, while the original-vs-compiled ARM reports are the substantive candidate evidence.
- The reference report SHA-256 values match the review packet: seed 7 `2f60d1a89661e44b6e3d2bb6464aba9fbae38624ea7f83a0f42af0655451a7ed`; seed 20261024 `37576c0edffbd0990302d9f19fe6ca4452721135d1952c7bf3a83a71976871b3`.

### Bounded runner caveat

`execute_pair` observes and serializes writes but its pass predicate does not explicitly require the accumulated write sets to remain empty (nor compare write sets). For these exact reported source/object hashes, source inspection shows only comparisons and returns, the reports show empty data/stack write sets, and original disassembly contains no stores, so this does not overturn the present bounded result. Before reusing the runner for a different candidate family, make unexpected writes fail explicitly and expand access instrumentation to the memory regions that family can touch. The test runner also intentionally does not require identical table-read footprints.

## Promotion boundary and missing evidence

Trial integration is reasonable because the callers pass byte values directly and store only the returned indices, and all values in that call domain have been exhaustively compared. The integration owner should still run the actual initializer/caller composition and verify the fields at `+0x28/+0x2C/+0x30` against the three original outputs on matched state. This task did not test how the UI labels those indices, option editing or extreme navigation, cancellation after edits, confirmation, re-entry, eight-byte config-pair copy, save-file persistence, or a restart. It did not patch the full initializer, run a caller window, compare original versus integrated patch in Azahar, or prove the loader/runtime path. H2's acceptance list requires those broader observations before claiming settings-menu behavior or milestone completion.

The reports and function records accurately keep `caller` and `runtime` at `not_run`. Do not extrapolate the isolated mapper result to the full initializer or audio settings workflow.
