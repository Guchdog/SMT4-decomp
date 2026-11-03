# H2 paired input flag getters — 2026-11-02

Converted `0x002BB978` and `0x002BC9C8` from naked assembly to typed C++ signed-byte reads at `0x0044E362` and `0x0044E381`. Both production bodies fill their 16-byte slots and have no relocations. Their compiled final-address bytes differ from the pinned original, so both ledger rows are `non_matching`.

The pinned-image offline differential passed 512 direct cases (all byte values for each getter), checking sign-extended `r0`, `sp`, and `r4-r11`. Twenty-five compositions through original reader `0x0011C5EC` compared original and patched reader outputs, memory writes, and helper call traces across zero, positive, and high-bit values for each flag. The second getter's conditional call and clear path were exercised. An unsigned-load mutation for the first getter was detected. The ARM caller instructions at `0x0011C6B0` and `0x0011C6C0` were confirmed to branch to the intended even ARM entries. Two-slot IPS replay passed and changes were confined to these slots.

Coordinator report: `build/agent-work/H2-semantic/h2-input-signed-flag-getters-convert/run001/coordinator/report.json`; runner: `tools/h2_input_flag_getters_experiment.py`. The report pins the reference image and records object, body, IPS, and staged-image hashes.

Evidence is bounded to mapped ordinary memory and a controlled ring-reader seam. It does not prove physical input provenance, MMIO behavior, access-width observability under concurrency, scheduling, or full H2 runtime equivalence.
