# H2 production conversion: `0x00128610`

## Scope

Converted the input-sample normalization dispatcher used by
`0x0011C5EC`. The implementation follows the static contract in
`h2-input-normalizer-contract-00128610.md` and retains all three normalization
callees as original ARM. Selector routing is typed C++; compiler-constrained
sample registers keep the wrapper within its original slot while preserving
the input ABI.

## Offline evidence

Command:

```powershell
python tools/h2_input_normalizer_experiment.py --out build/agent-work/H2-semantic/h2-input-normalizer-convert-00128610/run001/checks/coord-final-20261104
```

Result: 254/254 direct cases and 12/12 original-reader caller compositions
matched. Direct cases run the three original normalizer callees and validate
the selected branch, `r0-r3`, both outgoing stack words, and 8-byte call-stack
alignment. The comparisons include raw `r0`, callee-saved `r4-r11`, SP, faults,
full fixture context/output, and ordered writes. Four negative controls were
detected. Candidate body is 144/148 bytes with three even-target `R_ARM_CALL`
relocations; the original reader's callsite is an even ARM `BL`. Slot-only IPS
replay passed. Both affected production TUs compiled to private objects.

## Provenance and limits

- Pinned `code.bin` SHA-256:
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Source/runner, report, staged image/IPS, and object hashes are in the
  implementation handoff.
- Direct and caller fixtures use valid, disjoint ordinary RAM. The actual
  normalizer callees remain original code; the ring reader is controlled.
  Physical input provenance, source freshness, scheduling, aliasing, malformed
  pointers, MMIO/device effects, and whole-title runtime behavior remain open.
- Candidate bytes differ from the original; ledger classification is
  `non_matching`.
