# Independent review — H2 logical mode-0 query

## Finding

The typed production query is a boundedly supported reconstruction of the pinned mode-0 helper contract. The pinned ARM and C++ agree on unsigned ID validation, mode-flag branch, first-counter pulse, unsigned threshold gate, retained quotient/remainder call, remainder-based return, and caller-visible ABI/data effects. H2 Calc uses IDs `4` and `3`, with mode-0 fallback IDs `0xD` and `0xC` respectively. This supports isolated helper promotion only; it does not establish producer freshness, physical controls, H2 event delivery, or runtime equivalence.

The helper deliberately retains the original service at `0x002C6C10`. The candidate passes `(counter-threshold, selector)` in `(r0,r1)` and consumes its remainder result in `r1`; it does not reconstruct or replace that service. Selector zero is excluded because it enters the original divide-by-zero path.

## Pinned branch and caller contract

The image hash recorded by the report matches pinned US v0.1.0 `code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`). At `0x002B902C`, ARM does the following:

- `cmp r0,#0x1f; bhs` returns zero for unsigned IDs `>=31`.
- It tests bit 0 of the word at `0x004650A8`. When set, it zeros the effective counter and skips the counter table; when clear, it reads `*(u32*)(0x004E3C58 + 4*id)` and returns one immediately if that value is exactly one.
- It loads the unsigned threshold from `0x004650AC`; `counter <= threshold` returns zero.
- Otherwise it loads selector `*(u32*)0x004650B0`, computes `counter-threshold` (safe from unsigned underflow due to the preceding comparison), and calls `0x002C6C10`. The return path tests `r1` and returns one iff the remainder is zero; otherwise it returns zero.

The C++ retains the same control flow, uses `u32` for ID/counter/threshold/selector, and calls the original helper through explicit ARM inline assembly with declared register/memory clobbers. H2's static caller evidence is the producer audit's `(4,0)->ui_func_002B902C(4)` with false fallback `0xD`, and `(3,0)->ui_func_002B902C(3)` with false fallback `0xC`. The query itself does not name a physical button or establish when those counters refresh.

## Differential and effects

The final differential report SHA-256 is `6807afa87dc042e3d721c17c51027f1ffd97106ada678cfa5e1e7899b6b9f936`. It reports `140,864` valid matrix cases (`31 IDs × 4 flags × 4 thresholds × 4 nonzero selectors × 71 counter values`) plus 20 invalid-ID cases, `140,884` calls total. Counter coverage is `0..65`, `127`, `255`, `0x7fffffff`, `0x80000000`, and `0xffffffff`; thresholds are `0,7,31,64`; selectors are `1,2,3,7`. It compares return, fault, PC, SP, and preservation of `r4-r11` and checks the returned value against the mathematical contract. The service hook observes `43,896` entries, equal between original and candidate and equal to the branch-derived expected count: only valid IDs with flag bit 0 clear, counter other than one, and counter above threshold call it.

The harness records service-entry counts, not per-entry argument traces. The exact arguments are supported by the pinned instructions and candidate source; result behavior is differentially checked against the original and expected remainder predicate. The three directed controls detect wrong counter, threshold, and selector behavior, each with different returns; the wrong-selector case also confirms a service call occurs in both paths.

No non-stack guest data writes were recorded. SP, PC, faults, returns and `r4-r11` are compared. The report shows stack-write counts of `281,774` original and `175,584` candidate across the sweep; these are not asserted equal and stack-memory contents are not compared. This is consistent with different local prologue/scratch traffic and still supports the usual caller-visible function contract because SP is restored, but it is not exact stack-scratch equivalence. The standard ABI does not require identical temporary bytes below restored SP.

## Object identity and ledger

The compile report SHA-256 is `2703853e94dd720426fee728edd839a699f1d52cdd020a7abbcb9b18b4f08b66`; all seven listed production/caller objects exist and match their recorded hashes with successful exits. The production definition is 136 bytes, relocation-free. I independently extracted the current candidate and production objects: candidate object SHA-256 `617b1f99adbc6620c3dd60029c13ae6506e0bd7aa1a54be6b75be27e3243ee7e`, production object SHA-256 `0596cea541cb609cb60f0ee43b66a62071c0f2050509cd4dad3a909de77b7605`; both good function bodies are 136 bytes with SHA-256 `6d375730a5326520f907ac12c3928dafdcfb2d85dc1fefcc86f727ef1c662538` and no relocations. The original span is 104 bytes. `config/functions.csv` truthfully classifies `0x002B902C` as `non_matching`; the body-size and identity evidence does not imply code-image installation.

## Limits and recommendation

Selector zero was excluded; the retained original service, including its exceptional zero-divisor path, remains an external dependency. The bounded input matrix does not establish that the state producer updates all relevant counters freshly or before Calc, and it does not identify physical controls or delivery. No IPS image or original-versus-patched H2 runtime scenario is covered. Recommend isolated promotion of the helper source contract with `non_matching` retained, while keeping the service dependency and input/runtime limits explicit.

No build, test, emulator, debugger, or guest-state action was run for this review.
