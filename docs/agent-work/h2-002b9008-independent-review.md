# Independent review: 0x002B9008 manager counter helper

## Recommendation

Approve the conversion as a bounded semantic reconstruction of the direct helper contract on valid, mapped ordinary memory. The fresh final-VMA run matched all 32 cases, including the signed threshold boundary, changed incoming registers, raw `r0`, memory effects, and ABI observations. Keep the `non_matching` classification: the compiled 36-byte body is not byte-identical to the original. This review does not establish shared scheduler/manager lifecycle behavior or caller-specific semantics.

## Frozen inputs and fresh run

Recomputed all 21 `input_sha256` entries in the run001 packet; all match. The pinned original image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`; pinned candidate source SHA-256 is `c7c21625bf8c5b13ac9072f1a92b304abac74709daa44b7b2d22ccb7065d2fff`.

Ran a fresh isolated seeded case set:

```text
python tools/h2_b9008_experiment.py --out build/agent-work/H2-semantic/h2-manager-counter-adjust-002b9008-review/run001/checks/fresh-seed-20261119 --seed 20261119
exit: 0
```

The report at `checks/fresh-seed-20261119/report.json` has SHA-256 `e3a4bc123db4a8a711c066ab2adc40ce289064db92994906dbff2eac4283b16a`, seed `20261119`, and fixture SHA-256 `8620b5caa61476c8ca04ca4b2fb1193b0cf2dd4c189b43340e56f8904e2455a5. The fixture digest differs from the implementation run (`ff4021ea2f66936e0ad5786ebc28f22d8c563d27451b9260deacbf3eab0b7ac0`), confirming a distinct generated fixture. Result: `all_passed=true`, 32/32 direct cases, zero mismatches, both mutation controls detected.

## Contract and ABI audit

The original ARM at `0x002B9008` loads the literal global address `0x0043DCB0`, dereferences word `[global+4]` at `0x0043DCB4` to obtain the manager pointer, adds `0x600`, then loads a **signed** halfword at manager+`0x64A`. It decrements and stores that halfword only when the signed value is greater than 10, then returns. The original leaves raw `r0` equal to manager+`0x600`; incoming `r0` is ignored.

The candidate preserves this order and signed comparison. The 32 fixtures cover values `-32768, -1, 0, 9, 10, 11, 12, 32767`, each under incoming `r0` values `0`, `1`, `0xDEADBEEF`, and the manager base. Values through 10 remain unchanged with no write; 11, 12, and 32767 decrement by one. Every case returns raw `r0=0x500600`, with original/staged state equal, including stack pointer and callee-saved register checks. The observed store, when taken, is a two-byte write at manager+`0x64A`. The runner snapshots the manager region and checks the configured global bytes; no out-of-contract memory effect appeared.

The object emits a 36-byte body for the 36-byte slot, with no relocations and ARM entry bit 0 clear. The body SHA-256 is `b80321a4a7ef17f8513b315497eadc6cae9a6c8bdd4cd01efe57111c3afcf7b0`; `body_byte_identical=false` is expected and the report explicitly records it. The generated slot-only IPS replays exactly against the staged image (`exact_slot_ips_replay=true`), and the staged image differs from the base only in the helper slot (`only_slot_changed=true`). The runner's two negative mutations—lowered threshold and wrong halfword offset—are both detected. Thus the report exercises the stated contract rather than merely trusting a passing flag.

Declarations in the two engine callers and the UI alias are no-argument `void` declarations. That supports the call ABI and ignored-input-argument contract; callers do not consume the raw `r0`. It does not show that helper effects alone reproduce the wider status-down flow, manager setup, or scheduler lifecycle. The `0x002CAEF0` record describes the broader callback context; no caller-composition or runtime result is claimed here.

## Classification, totals, and limits

`config/functions.csv` truthfully labels `0x002B9008` `non_matching`. README totals reconcile with the ledger: 10,912 matching functions (3,121,300 bytes), 8 matching spans (484 bytes), and 47 non-matching functions (17,324 bytes), for 3,139,108 bytes total. The README's combined exact-byte total of 3,121,784 includes the 484 span bytes; its function total is 10,959 plus 8 spans.

The evidence supports only the helper's direct behavior for valid mapped ordinary memory with the global+4 manager pointer. It does not test null, unmapped, aliasing, concurrent, or MMIO accesses. Volatile accesses retain memory operations in the C++ implementation but do not establish atomicity or thread synchronization. No natural runtime reachability, shared manager lifecycle, scheduler semantics, or equivalence of the UI alias's broader effects is established. Keep those as open integration questions; no concrete counterexample was observed in the bounded domain.
