# H2 conditional global store conversion: `0x0028DF3C`

## Result

Replaced only `ui_func_0028df3c` in `src/engine/leaf_batch22_b.cpp` with typed C++. It keeps the unsigned wrapping predicate `(value + 1u) < 3u`, conditionally writes the original word to `0x0043E0BC`, and always returns raw `value`. Other callers and declarations remain untouched. `leaf_batch30_c.cpp` declares a `uint32_t` raw return that feeds the state getter; `leaf_batch45_a.cpp` declares the symbol `void` and discards the raw return after a `0xFFFFFFFF` call.

The affected TU compiled with one compiler slot. The body is 24/24 bytes with no relocations and was staged at its original VMA. IPS replay matched exactly and changed no bytes outside the 24-byte slot.

## Validation

```text
python tools/h2_8df3c_experiment.py --out build/agent-work/H2-semantic/h2-callback-global-condition-0028df3c-convert/run001/checks/seed-20261104-final --seed 20261104
```

Exit 0: 59 direct original-vs-production cases and 18 compositions through original callback `0x00221168` passed with zero differences. Direct cases include 0, 1, 2, `UINT32_MAX`, neighboring/high values and 48 seeded words. The callback ran the helper real, then original state/context/value getters, with `0x00286928` controlled; its call order, raw args, stack words, conditional store and raw return were compared. The helper call at `0x00221174` resolves to even ARM entry `0x0028DF3C`.

Both controls failed as expected: non-wrapping `value < 2` and storing `value + 1`. Report SHA-256 is `f9e9e37c01ac127bb24782e52ce9d9285906a2ada0bc095c5cda600d99b47a92`.

## Limits and ledger follow-up

The callback fixture uses mapped ordinary RAM; final helper semantics and the broader H2 runtime were not tested. The independent run002 review accepted the bounded evidence, and the full ARMv6K build passed 204/204 translation units (see `h2-0028df3c-integration.md`). No emulator was run. The coordinator corrected the ledger row to `non_matching`, because the compiled body differs from the original bytes.
