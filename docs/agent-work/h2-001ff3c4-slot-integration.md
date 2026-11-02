# `0x001FF3C4` accumulated H2 slot integration — run002

The reviewed 880-byte C++ sequence was installed in place at `0x001FF3C4` on the accumulated H2 image that already contains the reviewed `0x0029F278` cursor updater. All ten ARM calls resolve to the original `0x00254CA8` query service. The 152-byte forward and 148-byte reverse helpers are contiguous after the 580-byte main body. The remaining 224 bytes of the 1,104-byte original slot are preserved.

Run002 generated an IPS for exactly that slot and verified IPS roundtrip. It compared the accumulated base with the same image plus this slot replacement through four `TitleConfig_Calc` compositions: stable cursor, active cursor without input, logical input bits, and initialized H2 cursor. All four passed. The harness retains the original axis query/input/calibration chain and models unrelated outer Calc services. Independent run003 reproduced the hashes, audited every changed byte, confirmed the 224-byte suffix and all ten ARM call targets, and passed all four compositions. The direct differential remains documented in [the function record](../function-records/0x001ff3c4.md) and [run006 integration](h2-001ff3c4-integration.md).

| Evidence | Result |
|---|---:|
| Accumulated base SHA-256 | `d16516c9ce191d88f728d14dcc08bf4bf2a6d3a81ee11603f4b00253e8b1c9cb` |
| Accumulated result SHA-256 | `37cb6046f1be329d7af06ef36430a52897b49c0f96d5b5fdb4353bef39fd4876` |
| Slot IPS SHA-256 | `8dc60d81cbaed38086924c717d6213581434ea1145aa614c1c2f751c97b4ad38` |
| Integrated body SHA-256 / size | `44c6adab3101df0623cdeeea1b69459c41c7d0bfb4c8f12bd9fe62db9dd04717` / 880 bytes |
| `TitleConfig_Calc` composition cases | 4/4 passed |
| Slot suffix / IPS roundtrip | preserved / passed |
| Independent slot review | accepted; fresh run003 reproduced artifact and caller cases |
| Report SHA-256 | `c381c2eb2c2b8d8769960c95c1cffae46c374c4fbc691f7fa421da4ec13e7fc6` |
| Runtime | not run |

## Address arithmetic correction

An independent byte comparison of run002's base and result confirms the changed half-open address range is `[0x001FF3C4, 0x001FF734)`. The original slot ends at `0x001FF814` (`0x001FF3C4 + 1104`), leaving the 224-byte suffix `[0x001FF734, 0x001FF814)` unchanged. The independent review's prose gives `0x00200444` for the range end; that is an arithmetic typo. The report's stated 880-byte body, 224-byte suffix, IPS roundtrip and byte comparison remain consistent with the corrected addresses.

Reproduce with:

```powershell
python tools/h2_1ff3c4_integrate.py --output build/h2-1ff3c4-integrated/<fresh-run>
```

This is an offline integrated image artifact, not an Azahar runtime comparison or whole-game equivalence claim. Physical input and scheduling remain unresolved.
