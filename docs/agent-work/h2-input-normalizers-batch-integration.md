# H2 three-selector input-normalizer integration

## Staged slice

The integration runner compiles the three production C++ children and stages
only their original slots: selector 0 `0x0013B9FC` (208/228 bytes), selector 1
`0x0013B8F8` (252/260 bytes), and selector 2 `0x0013BAE0` (368/460 bytes).
The pinned dispatcher callsites continue to target their even ARM entries.
Selector 0/1 divider calls are resolved to the original even ARM helper
`0x002C615C`; selector 2 has no relocations. The combined IPS round-trips, and
the audit confirms no changed bytes outside those three slots.

## Caller evidence

`tools/h2_input_normalizers_batch_experiment.py` compares the pinned original
with the three-slot staged image through the original input reader
`0x0011C5EC` and sample dispatcher `0x00128610`, using a controlled
`0x0012A758` ring-reader seam. Seed `20261112` matched 402/402 caller cases:
132 for each selector across two seeds, three calibration pairs, signed axes,
quadrants, zero and boundary samples, plus early count gates and an unsupported
selector. The full caller result comparison includes return, output/context
bytes, write traces, reader calls, preserved registers and stack state.

The three implementation TUs and dispatcher consumer TU compiled to private
objects. This is a bounded integrated replacement of the selector children;
the reader/dispatcher and their remaining dependencies execute from pinned
original code. It does not establish live input provenance, cadence, emulator
runtime behavior, FPSCR exception-flag parity, or whole-title equivalence.

Primary report:
`build/agent-work/H2-semantic/h2-input-normalizers-all-selector-integration/run001/checks/coordinator-seed-20261112/report.json`.
Independent integration review is the next gate.
