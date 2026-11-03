# H2 callback value getter conversion: `0x00296F60`

## Result

Replaced the naked function body in `src/engine/leaf_batch42_a.cpp` with readable typed C++. It derives the slot using `count - selector - 1`, dispatches types 0–4, preserves the raw word path, and implements signed float conversion through the ARM compiler's `VCVT.S32.F32`. Types 2 and 3 use the word stored in the selected slot as an index into their separate global arrays at `0x004C4744` and `0x004C4D44`.

The affected TU compiled with one compiler slot. The extracted candidate body is 156/164 bytes and has no relocations. It was staged at `0x00296F60`; the callback's original ARM `BL` at `0x002211C0` targets that even ARM address.

## Validation

Command for the refreshed run002 packet:

```text
python tools/h2_96f60_experiment.py --out build/agent-work/H2-semantic/h2-callback-value-getter-00296f60-convert/run002/checks/seed-20261103-float-cartesian --seed 20261103
```

Exit 0: 109 direct cases and 24 compositions through original callback `0x00221168` passed with zero differences. The direct matrix now asserts all 48 Cartesian float cases: both conversion types (1 and 3), each of the four valid selector positions in a four-entry table, and all six finite boundaries (`0.0`, `-0.99`, `1.99`, `-1.99`, `2147483520.0`, `-2147483648.0`). It also covers selectors 0–4 in a five-entry table, first/last entries, all other documented types, unknown type bytes, typed array indices, and additional directed cases. The callback ran original set-global, state getter and context getter code with the selector real; the final helper return was controlled. Comparison included reads/writes, relevant call arguments and order, callback raw return, SP and callee-saved registers.

Both negative controls were detected: shifting the work slot value read by four bytes and substituting the selector index for the slot's stored global-array index. A separate type-2 case with array index `0x4000` faulted in the pinned original outside mapped memory; it is recorded as an unsupported-domain probe rather than counted as a differential pass.

Fresh run002 report SHA-256: `b03d3d4c242d6f2b9572f55b1fcd98b870adfb5f8b1aee3557d90c2a8d2c59f1`. It records the pinned reference, frozen production source, object, body, IPS and staged image identities. The production source SHA-256 is `d9ad8b4bbd8952daab3c199ca2379561fc16c4901ae41ebd230213ce5098b4ac`; the body remains 156/164 bytes with no relocations.

## Limits and ledger follow-up

The tested float domain excludes NaN, infinities and finite values outside signed-32 representability. The helper has no checks for an empty table, invalid selector, malformed pointers or array indices. The original callback composition controls the final helper at `0x00286928`; it does not establish that helper's semantics or whole H2 runtime behavior. No full build or emulator was run.

The coordinator corrected the ledger row to `non_matching`, because the compiled code is not byte-identical to the pinned original. The independent review accepted the repaired evidence run002; the full ARMv6K build passed 204/204 translation units (see `h2-00296f60-integration.md`).
