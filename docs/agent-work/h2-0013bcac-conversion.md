# H2 input postprocessor conversion — `0x0013BCAC`

## Result

Replaced the 212-byte naked ARM body with typed C++ in
`src/engine/leaf_batch16_c.cpp`. The compiled body is 148 bytes with no
relocations, padded within the original slot, and classified `non_matching`.
The implementation preserves sequential bit transitions, word-store order and
the final raw `r0` return.

## Validation

`tools/h2_13bcac_experiment.py` compiled the production TU, staged its function
at `0x0013BCAC`, and replayed a slot-only IPS. The pinned original and candidate
matched over 192 direct cases (64 transition-bit combinations plus 128 seeded
full-word cases). A mutation removing the current-bits conjunction was
detected. Another 32 cases ran through the original `0x0011C5EC` reader with a
controlled ring seam; the optional postprocessor ran in 16, and the reader's
saved context word matched output `+0` at helper entry.

The complete ARMv6K build passed 204/204 translation units. Independent review
passed fresh seed `20261217` with 192 direct cases, 32 reader compositions and
the mutation control; it found no counterexample. See the
[independent review](h2-0013bcac-independent-review.md). The domain excludes
concurrent observers, MMIO, invalid mappings and physical input provenance.
The reader caller remains the original pinned body during composition, and
this does not establish end-to-end input or H2 lifecycle behavior.
