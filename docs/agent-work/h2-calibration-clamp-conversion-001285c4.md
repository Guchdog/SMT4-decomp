# H2 production conversion: `0x001285C4`

## Scope

Converted the direct calibration-clamp dependency of H2 input reader
`0x0011C5EC`. The contract and independent static contract review are in
`h2-input-state-reader-contract.md` and
`h2-input-state-reader-contract-review.md`. The target body remains in its
original 76-byte slot. No caller interface or shared runner interface changed.

## Offline evidence

Command:

```powershell
python tools/h2_calibration_clamp_experiment.py --out build/agent-work/H2-semantic/h2-calibration-clamp-convert-001285c4/run001/checks/coord-verified-20261102
```

Result: 334/334 direct cases and 16/16 compositions through the original
`0x001078D8` caller and `0x0011C5EC` reader matched. The three mutation
controls were detected. Candidate body size was 76/76 bytes with no
relocations; its exact-slot IPS replay changed only the `0x001285C4` slot. The
original reader's BL from `0x0011C61C` targets the even ARM address
`0x001285C4`.

The tests compare the complete fixture context, ordered memory writes,
r0-r12, SP, LR, and fault result. Inputs span two reproducible seeds and all
signed-halfword clamp boundaries. A further 16-caller-case composition runs
the original reader and callback caller with only the clamp slot replaced;
`0x0012A758` is controlled to provide count/sample fixtures. The affected
production and consumer TUs compiled successfully to separate private object
files.

## Provenance

- Pinned `code.bin` SHA-256: `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Source and runner hashes, output report, staged slot/image, IPS, and the two
  private TU objects are recorded in the implementation handoff.
- Exact byte matching is not claimed. The production row is pending
  coordinator promotion to `non_matching` after independent review.

## Limits

Valid, disjoint synthetic ordinary RAM only. The ring reader is a controlled
seam. No claim is made about physical input identity, live scheduling,
malformed pointers, aliasing, MMIO/device effects, natural runtime reachability,
or whole-title H2 equivalence.
