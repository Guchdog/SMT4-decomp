# Independent review — H2 input refresher + state reader chain

## Recommendation

Approve the composed `0x001078D8` → `0x0011C5EC` behavior only for the valid, disjoint synthetic-memory contract exercised by this chain. Fresh final-image execution matched the pinned original in all 144 cases; no counterexample was found. Both ledger rows are correctly `non_matching`.

## Frozen inputs and independent rerun

I recomputed all 18 input SHA-256 pins in the packet; every one matched. The pinned image SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Both production TUs, the chain runner, component runners, records, report, staged image and IPS match the packet pins.

Fresh command:

`python tools/h2_1078d8_11c5ec_chain.py --out build/agent-work/H2-semantic/h2-input-refresh-reader-integrated-chain-review/run001/checks/fresh-seed-20261117 --seed 20261117` — exit 0.

The fresh report SHA-256 is `0decd5f1b5444ee21a3d7a41973a74183bde2af7b65d2049c222e0243ec3b2f5`; staged image SHA-256 is `02d2642f5511f8cc81a493d324214e63507f9fdd571703e7c271a1f8affa1923`; combined IPS SHA-256 is `eaafacb43cf4eadc07826abcd25d78ed26f448058fde6f6ebb5e03b1d1ad1c6f`. The fresh fixture digest `0f315fea270ed7820ace12551ea98a17c0cbf2a68d8e274ae43efe4070c1d9e6` differs from implementation-run digest `d401374d32753db3bd3a6eb84e2d1195fe91944431d83d574fa473f44c2d5e95`.

## Two-slot placement, relocations and replay

The report and independently inspected staged image show the 304-byte reader at `0x0011C5EC` and the 164-byte refresher slot at `0x001078D8` (its C++ body is 160 bytes plus one ARM NOP). The slot payload SHA-256 values are respectively `020ce25c1e3238a586b05bb011b31efd603942d51685a214ba617111c9bee815` and `9dc986366822b2ea4de2f9918e8643c85f7fbdfb5e43c553825ad57edc88f97b`.

The refresher's single `R_ARM_CALL` at body offset 20 resolves from `0x001078EC` to the reader's even ARM entry `0x0011C5EC` (`0xEB00533E`). The reader's seven `R_ARM_CALL` sites resolve to even ARM entries `0x00128C2C`, `0x001285C4`, `0x0012A758`, `0x00128610`, `0x002BB978`, `0x002BC9C8`, and `0x0013BCAC`. The seven reader callees are the original ARM code; `0x0012A758` is controlled by the fixture seam during execution.

I replayed the two-record IPS against the pinned original with the repository IPS applier: replay exactly equals the staged image. The IPS has two records, and a bytewise original/staged comparison found zero changed bytes outside the two declared slots. The fresh run compiled both affected TUs; their objects hash to `bf2f8e3087a414133d18b3ddc3dd39e90a4822cc31f73846cc0f5d59dc0a5289` (reader) and `dd85dda953d3b7b90a1f802c690c034098a71e3f25f1d5661866b8053d185f5f` (refresher).

## Full-chain execution and ABI checks

All 144 original-versus-staged executions matched, with no faults or mismatches. The matrix covers mode bytes 0/4, signed ring counts -1/0/1, selectors 0–3, global flag pairs `(0,0)`, `(1,0)`, `(1,1)`, postprocess gate 0/1, randomized context/output/ring record bytes, 31 table rows and all 32 counter words. Each report row is equal and has `abi_ok: true`; the row-31 counter sentinel remains `0xDEADBEEF` in every case.

There are 72 ring calls across the mode-0 cases; mode-4 cases short-circuit before the ring helper. I checked every recorded trace: fixture source identity is true, output is `0x004E3C28`, requested count is 1, count/timestamp/index pointers are in the wrapper frame, and SP is 8-byte aligned. The runner's final pass predicate checks these conditions for calls from both original and staged executions. Its per-result comparison includes the complete context and state buffers, availability, all counters, ordered relevant writes, ring trace, SP, callee-saved registers and faults.

This composes both production slots at their original VMAs through the original refresher entry. It is stronger than isolated function comparisons for this defined chain, while remaining a synthetic fixture.

## Limits and next action

The `0x0012A758` ring reader is controlled and supplies signed count/sample records. The other reader callees execute pinned original code. This does not prove physical input identity or provenance, freshness of all state fields, actual ring behavior, scheduling/cadence, concurrency, MMIO, natural runtime reachability or whole-title behavior. No emulator or full build was run.

Retain the two `non_matching` classifications and the bounded component-chain result. Keep input provenance/freshness, scheduling and runtime behavior open; any broader claim needs separate evidence for those domains.
