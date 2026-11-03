# Independent review: integrated H2 input normalizers (selectors 0, 1, 2)

## Recommendation

**Ready for bounded integration review.** The fresh three-slot batch run matched all 402 original caller compositions, with 132 positive-count cases for each selector and no mismatch. All four affected TUs compiled sequentially in the runner's one-slot path. The combined IPS changes only the three declared slots, all dispatcher targets are even ARM addresses, selector-0/1 divider relocations resolve to the original even ARM `0x002C615C`, and selector-2 is self-contained with no relocations.

This evidence covers the controlled reader composition and valid disjoint synthetic ordinary RAM. It does not establish live input provenance, runtime cadence, title behavior, or FPSCR exception-flag parity. The branch-2 exception limit remains explicit.

## Slot and callsite audit

The pinned image is SHA-256 `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. The original function spans are adjacent and non-overlapping:

| Selector | Start | Original slot | Compiled body | Relocations |
|---:|---:|---:|---:|---|
| 1 | `0x0013B8F8` | 260 bytes, ends `0x0013B9FC` | 252 bytes | 3 calls to even ARM `0x002C615C` |
| 0 | `0x0013B9FC` | 228 bytes, ends `0x0013BAE0` | 208 bytes | 3 calls to even ARM `0x002C615C` |
| 2 | `0x0013BAE0` | 460 bytes, ends `0x0013BCAC` | 368 bytes | none |

Pinned dispatcher callsites resolve as ARM `BL`s to even entries: `0x00128678 → 0x0013B9FC`, `0x00128698 → 0x0013B8F8`, and `0x00128658 → 0x0013BAE0`. Selector-0 relocation offsets are 96/176/192; selector-1 offsets are 176/216/232. Every resolved divider target has bit 0 clear. Selector-2 compiles inline VFP sqrt and has no external relocations.

I independently decoded the emitted three-slot IPS records. It contains exactly `(offset 0x3B8F8, 260 bytes)`, `(0x3B9FC, 228 bytes)`, and `(0x3BAE0, 460 bytes)`. IPS replay equals the staged image; the runner's byte audit confirms no bytes changed outside these spans.

## Fresh offline evidence

Command (exit 0):

```text
python tools/h2_input_normalizers_batch_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizers-all-selector-review/run001/checks/review-seed-20261113 --seed 20261113
```

- 402/402 original reader/dispatcher caller compositions matched: selector counts 132/132/132, plus count-zero and negative-count early gates and invalid selector 3 across two seeds.
- Caller path used original `0x001078D8`, `0x0011C5EC`, and `0x00128610`, with only the three normalizer children staged; `0x0012A758` remained a controlled ring-reader seam.
- All three production implementation TUs and the dispatcher consumer TU compiled sequentially into private run001 objects through the runner's one-compiler-slot flow: `leaf_batch30_a.cpp`, `leaf_batch28_a.cpp`, `leaf_batch44_c.cpp`, and `leaf_batch29_a.cpp`. The consumer compile returned 0.
- FPSCR exception flags are not compared. No FPSCR parity is claimed. Runtime/emulator checks were not run.

Report: `build/agent-work/H2-semantic/h2-input-normalizers-all-selector-review/run001/checks/review-seed-20261113/report.json` (SHA-256 `1032dc891d22359989d52827c988aa0c90fb1f41f916751c9d52e2782c4a0d82`). Staged image SHA-256 `5ba67461679f3efc83bd482d26da897f549b722d3f82614919c2ff945d1475c4`; three-slot IPS SHA-256 `acc4b06f03598b06697ee9ec15d25c5e9299c4b801b1586817bc4cca75bad950`.

Private object hashes: selector-0 `leaf_batch30_a.o` `e39b538b01ba53ed49cc5cdd231862d4d25d64a2e255092483b0bd7776a2bf33`; selector-1 `leaf_batch28_a.o` `256aed41ef9d118aa66dd831b44c5d170606de296b83c1cc671d3d16334bb06d`; selector-2 `leaf_batch44_c.o` `f46154067a8aca79e270014fc7a26b5e16d5e41f49e5573c34fce34eed8fd7eb`; dispatcher consumer `leaf_batch29_a.o` `a99542f991ab01fdeb4381d7a399d77610dee760d931e5a99adbf3dbf3fac70c`.

## Limits and next action

The caller scenarios use controlled ring fixtures and ordinary synthetic memory. No producer liveness, physical input source, freshness, cadence, MMIO, aliasing, malformed pointers, whole-title behavior, emulator runtime, or FPSCR parity is established. Original reader/dispatcher code and its remaining services stay pinned dependencies; branch-0/1 retain the original signed divider dependency.

Coordinator may continue with the defined H2 integration boundary while retaining the controlled-reader and FPSCR limits and truthful non-matching byte classification.
