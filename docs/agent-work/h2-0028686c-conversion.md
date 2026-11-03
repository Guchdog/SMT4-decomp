# H2 callback getter conversion: `0x0028686C`

## Result

Replaced the naked 20-byte getter in `src/engine/leaf_batch21_b.cpp` with typed C++ taking and ignoring its incoming word. It reads the volatile pointer at `0x0044DEB8` and returns the raw word from pointer `+0xC0`, without writes or pointer validation. Its compiled body is 20/20 bytes with no relocations and is staged at the original ARM entry.

## Validation

`tools/h2_8686c_experiment.py` compiled the production TU, staged a slot-only IPS, compared original and candidate direct behavior, then composed the staged getter into the original `0x00221168` callback. The original `0x0028DF3C` and `0x00289640` getter calls ran directly; the other complex selector/final helpers were controlled and their events/arguments were compared. The wrong-offset mutant replacing `+0xC0` with `+0xC4` was detected in direct and callback cases.

Run seed `20261231` passed 38 direct cases and 50 callback compositions with no differences. It compared pointer-chain reads, no-write behavior, raw values, helper call order/arguments, callback raw return, stack alignment, `r4-r11`, and observed memory effects. IPS replay was exact and changes stayed inside the 20-byte slot.

Report SHA-256: `323ad7b7eb101772a6f081d135672c60fa506a262b9a4472d40719646aa549db`. The details and per-case traces are in `build/agent-work/H2-semantic/h2-callback-getter-0028686c-convert/run001/checks/seed-20261231-verified/report.json`. The original callback `BL` at `0x002211B4` targets the even ARM entry `0x0028686C`.

## Limits and ledger follow-up

Independent review run002 accepted the bounded evidence after checking the corrected ledger and README arithmetic; the ARMv6K full build passed 204/204 translation units (see `h2-0028686c-integration.md`). The composition uses a synthetic mapped pointer chain and controlled seams at `0x00296F60` and `0x00286928`; it does not establish those helpers' complete semantics or runtime behavior. Invalid pointer faults and physical input provenance are untested. No emulator was run. The coordinator corrected the ledger row to `non_matching` because the compiled getter bytes differ from the pinned original.
