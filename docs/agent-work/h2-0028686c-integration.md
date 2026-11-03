# H2 integration closure: `0x0028686C`

After independent review accepted the bounded direct and original-callback evidence, the coordinator compiled the full ARMv6K translation-unit set with:

```powershell
python tools/build_check.py --repo-root . --out-dir build/agent-work/H2-semantic/h2-callback-getter-0028686c-integration/run001/full-build -j 8
```

Result: **204/204 translation units succeeded**, zero reused objects, eight compiler workers, elapsed 14.40 seconds. Outputs are confined to the ignored `build/` tree.

The ledger row for the 20-byte getter is `non_matching`, because its typed C++ body differs from the pinned original bytes. The callback composition remains partial: `0x00296F60` and `0x00286928` are controlled seams. No emulator/runtime comparison or full H2 lifecycle acceptance was performed. See the [function record](../function-records/0x0028686c.md), [conversion evidence](h2-0028686c-conversion.md), and [independent review](h2-0028686c-independent-review.md).
