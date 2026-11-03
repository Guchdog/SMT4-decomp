# Independent review: H2 input ring reader `0x0012A758`

## Recommendation

Approve the candidate for its bounded offline contract: direct ARM differential, source-header retry behavior, path-dependent raw `r0`, and eight compositions through the original `0x0011C5EC` wrapper all passed in an independent seeded run. This supports the typed conversion on valid aligned synthetic ordinary memory with canonical ring slots and deterministic source changes. It does not establish the source producer, payload/header coherence, real-time liveness, alias behavior, physical input provenance, or full H2 runtime behavior.

## Provenance and independent run

Every declared run003 input hash matched before execution, including the corrected contract, production source, runner, pinned original, coordinator report/staged image, function record, README, and ledger. The target source SHA-256 was `bd7cb87c5deaf50327476358d008456e62300e3d15bbea5bc5c6138f1f707e93`; the pinned original image SHA-256 was `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.

I ran:

```text
python -B tools/h2_input_ring_reader_experiment.py --out build/agent-work/H2-semantic/h2-input-ring-reader-0012a758-review/run003/checks/fresh-20261104 --seed 20261104
```

Exit 0. The fresh report SHA-256 is `80d8ac671f0d1ceaeffe4b2bdd03ffa244952c45e74e2bb972225212e2ac51f2`. Its deterministic compiled body SHA-256 is `2424bd9442b945cf79209700c742fdb6d0b1754e8b0c529d8e785519c8f15ca1`, size `404/424`, with no relocations. The 424-byte IPS replay passed; IPS SHA-256 is `88c25761740591b12066eafc092586d6f3d46f549e03fe7b0f63e11a68605ae0`. The staged image SHA-256 is `8811e4837fa8759e7f0631f4e5ea2cb04909161154169f12888d6f2f8d18cb6e`; an independent byte scan found all changed bytes inside `[0x0012A758,0x0012A900)`.

## ABI, return, and code review

The six arguments are `r0=source`, `r1=output`, `r2=signed request`, `r3=count_out`, entry `[sp]=cursor_out/in`, and entry `[sp+4]=index_inout`. The original prologue saves `r0-r11,lr`, but its epilogue advances over the saved argument registers and only pops `r4-r11,pc`; only `r4-r11` and SP are preserved by the function contract. `r12` and flags are scratch; no VFP registers are used.

The raw return is path-dependent, and both the instruction flow and fresh direct run confirm it. Before the stable commit, the original does not change `r0`, so early exits return the incoming source pointer (`0x00510000` in the fixture). On the stable path, the final `ldr r0,[sp,#0x4C]` loads and returns `index_inout` (`0x00530020` in the fixture). The stable example committed count 1 and index 3. The H2 wrapper ignores this raw helper result and gates on `count_out`.

The candidate retains the signed request cap of seven, signed 64-bit cursor comparisons, canonical modulo-eight source slot, five record loads/stores in the original order, partial output writes before snapshot validation, and the stable commit order (count, cursor high, cursor low, index). The fresh direct differential reported 1,225 directed plus 128 seeded cases with zero differences, including request/signed boundaries, availability branches, negative/zero computed counts, wrap, and all-ones caller cursor/index values.

## Retry, caller, controls, and classification

Five deterministic source-header mutations at offsets `0x0`, `0x4`, `0x8`, `0xC`, and `0x10` each fired after the first output store, caused a full retry, and produced ten record stores (two copies). A two-event mutation sequence caused two retries and 15 stores (three copies). Original and candidate traces matched in all cases.

The runner executed eight actual-reader compositions through original `0x0011C5EC`, using the candidate ring reader rather than the wrapper experiment's old controlled reader seam. All eight matched and the wrapper returned 1. The caller uses `r2=1`, local count storage, `cursor=UINT64_MAX`, and `index=UINT32_MAX`; thus each supported caller case exercises at most one 16-byte record. The wrapper output remains synthetic ordinary memory, not a live producer fixture.

All four negative controls were detected: cap 7 changed to 8, signed 64-bit compare changed to unsigned, ring mask 7 changed to 3, and cursor word store order reversed. The current `config/functions.csv` row labels `0x0012A758` `non_matching`, consistent with the byte-different 404-byte C++ body. README exact-byte arithmetic independently reconciles: `10,886` matching functions = `3,117,008` bytes, plus 8 matching spans = `484` bytes, for `3,117,492 / 3,139,108 = 99.3113967%` (reported as `99.3114%`); `73` non-matching functions total `21,616` bytes.

## Limits

The direct fixture maps valid, disjoint aligned memory and canonical effective slots 0..7. Its one-shot mutation hooks test retry mechanics but not a live writer. The caller compositions use a synthetic ring object with a stable header/payload, so they do not identify an actual object producer or prove the payload matches the header. The reader has no bounded retry count or explicit barrier; a continuously changing source can spin indefinitely. Source/output/parameter aliasing, malformed pointers, noncanonical indices, invalid-memory fault ordering, producer lifecycle, refresh cadence, device mapping, and natural/full-title reachability remain unproven. No full build or emulator was run.

## Checks

- `python -B tools/h2_input_ring_reader_experiment.py --out build/agent-work/H2-semantic/h2-input-ring-reader-0012a758-review/run003/checks/fresh-20261104 --seed 20261104` — exit 0; report at `build/agent-work/H2-semantic/h2-input-ring-reader-0012a758-review/run003/checks/fresh-20261104/report.json`.
- Read-only source/runner inspection confirmed the randomized seed reaches fixture construction, five individual source-header mutations plus the repeated sequence, four independent mutation controls, and eight original-wrapper/candidate-reader compositions.
- Independent IPS replay/scope and ledger/README arithmetic scripts exited 0; run003 packet pins matched.
