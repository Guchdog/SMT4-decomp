# Independent production review: paired script getters

## Recommendation

The source conversion is supported for aligned, side-effect-free ordinary RAM when the original halfword's two bytes are both readable. Keep both ledger rows `non_matching`; the original image still contains 12-byte `LDRH; AND #0xff; BX LR` functions, whereas the production C++ emits 8-byte `LDRB; BX LR` functions. The behavioral return contract, ABI state and exercised callers are supported in the stated domain. This review does not establish equivalence for MMIO, read-width-sensitive memory, page/fault boundaries, invalid/unaligned pointers, or full game behavior. The producer has not run a canonical full build or game runtime scenario.

## Frozen provenance and production source

Every frozen input hash in the review packet matched, including production `leaf_matching.cpp`, the ledger, candidate review tooling/tests, integration handoff and both seed reports. The production definitions are `u32 script_vm_func_002345f0(const u8* p) { return p[0x48]; }` and `u32 script_vm_func_002345fc(const u8* p) { return p[0x4a]; }`. These are alias-safe byte reads with unsigned zero-extension to `u32`.

The pinned original functions remain `b804d0e1ff0000e21eff2fe1` and `ba04d0e1ff0000e21eff2fe1`, respectively: `LDRH` at offsets `0x48`/`0x4a`, mask low byte, return. Ledger rows retain their addresses and 12-byte original spans but are classified `non_matching`, which truthfully reflects the emitted source. No issue found in source signature, offset selection, image identity, or ledger classification.

## Evidence inspected

Both producer runs compiled the production translation unit, extracted 8-byte relocation-free ARM leaves (`ldrb r0,[r0,#offset]; bx lr`), and compared pinned-original execution:

| Seed | Cases per getter | Differential | Controls | Caller windows |
|---|---:|---|---|---|
| 7 | 80 | passed | wrong offset and omitted mask detected | 4/4 passed |
| 20261024 | 80 | passed | wrong offset and omitted mask detected | 4/4 passed |

Directed halfword values include high-byte-only values and low-byte boundaries; 64 seeded values add coverage. Full `r0-r12`, SP/LR, PC, NZCV, data/stack memory and writes are compared. The runner deliberately suppresses only read-set equality because byte loads read one byte while the original halfword loads read two; it records both footprints. Each getter's isolated reports show original read addresses `{p+offset,p+offset+1}` and candidate `{p+offset}`. The data/memory comparison is performed in an ordinary-RAM Unicorn model.

Each seed tests one paired getter sequence in each of four actual direct-caller functions: `0x0038c43c`, `0x0038cdf4`, `0x0038d7b0`, and `0x0038de60`. Each window executes both calls and the subsequent moves consuming the low-byte results. The register-derived record pointer is passed in the observed `r10` or `r4` base plus `0x28`; the returned `0x5e` and `0xd3` values flow into their caller argument registers. Each window stops before the next external helper. Thus the caller evidence confirms both result uses in representative windows, but not all 16 sites per getter, every pointer/buffer shape, downstream behavior, or full callers.

The production verifier finds 16 aligned ARM `BL` references to each exact entry and no aligned pointer words or direct branches into either leaf interior. This is a useful static inventory, not a proof against Thumb, unaligned, indirect/computed, relocated or runtime-generated references.

## Read-width counterexample and scope

For any valid aligned ordinary-RAM object where both bytes are readable, ARM little-endian `LDRH` followed by `& 0xff` returns the same unsigned byte as `p[offset]`; the source return and caller-consumed values agree in all exercised cases. The machine access is still observably different: the original reads the adjacent high byte and the candidate does not. A minimal boundary counterexample is a pointer whose `p+offset` is the last mapped byte while `p+offset+1` is unmapped: original `LDRH` faults, while candidate `LDRB` can return successfully. That input lies outside the reported contract, which explicitly requires both original bytes to be readable.

Accordingly, do not reuse these reports for MMIO or any side-effect/read-width-sensitive memory, and do not claim identical fault behavior. If the actual script-record contract guarantees ordinary aligned RAM with both halfword bytes valid, this is a justified semantic conversion; otherwise require stronger object/bounds evidence or retain the halfword access with a type-safe implementation and rerun the evidence. The caller sites strongly suggest record memory, but do not alone prove every runtime pointer is in that domain.

## Remaining integration limits / next action

I found no actionable defect in the bounded differential or four caller windows. Treat this as independent support for the scoped C++ conversion, not full promotion/runtime acceptance. The integrator should confirm that the actual getter inputs always designate aligned RAM with both bytes readable, run the canonical affected build/regression, and decide whether H2 requires a patched-vs-original runtime scenario. Preserve the non-matching ledger labels. Producer reports are `build/agent-work/batch-h18-001/h18-integrate-002345f0-fields/run-001/checks/{seed-7,seed-20261024}/report.json`; their source, object, reference and report hashes are carried in the integration handoff.
