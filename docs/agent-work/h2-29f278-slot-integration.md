# H2 `0x0029F278` in-place integration — run002

## Result

The updater's 1024-byte ARM C++ body and its four-byte `.rodata.cst4` mask table
fit in the original 1536-byte slot. The builder writes them in place at
`0x0029F278` and places the table at `0x0029F678`; it does not allocate or branch
through the shared text-tail cave. All 15 external ARM call relocations target
pinned original helpers. The word-aligned image scan found no external direct
branches or aligned absolute pointers into the original body, and the 508-byte
suffix after the candidate code/table remains byte-identical.

Run002 passed 144/144 direct cases and six caller compositions: three against
the pinned original `TitleConfig_Calc` and three against the accumulated H2
image. In each caller run, `TitleConfig_Calc` and the cursor updater execute
from their respective original or accumulated images; the updater's direct
binary helpers remain in that same image. Unrelated outer Calc services are
modeled at the existing runner boundary. The wrong-helper-target sensitivity
control was detected, and the slot IPS round-trips against both base images.

| Evidence | Result |
|---|---:|
| Original image SHA-256 | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Accumulated H2 base SHA-256 | `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446` |
| Accumulated H2 plus cursor SHA-256 | `d16516c9ce191d88f728d14dcc08bf4bf2a6d3a81ee11603f4b00253e8b1c9cb` |
| Production source SHA-256 | `545cf3882ffe52d3f2a8346613ef546fe7a56d5835726d64d2f3923f1e54481a` |
| Production object SHA-256 | `927303525e167023ae1e784f15fb956face54d9e1d8903abd4ac3faeab7485f4` |
| Relocated body SHA-256 / size | `a31f235f0eb747504a63688c2411f17f90fa2c62fc7873947e81cdf12a603ef8` / 1024 bytes |
| Local table | `08 04 01 02` at `0x0029F678` |
| IPS SHA-256 | `e992245248917f8e802326b61d18e3da01af171d29387f37476b7572151ea5d8` |
| Direct / original caller / accumulated caller cases | 144 / 3 / 3 |
| Wrong-call-target control | detected |
| ARMv6K full build | 204/204 translation units passed |
| Runtime | not run |

Reproduce into a fresh ignored output directory:

```powershell
python tools/h2_29f278_slot_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-0029f278-slot/<new-run> --seed 20261104 --samples 128
```

## Limits

The accumulated-image cases compare the reviewed base image with a one-slot
overlay and retain the existing Calc harness's modeled outer service boundaries.
The fixtures use synthetic aligned ordinary RAM. They establish neither
physical input delivery nor natural scheduling, object lifetime, runtime audio,
or whole-game equivalence. Discarded memory reads and fault ordering, MMIO,
concurrency, and malformed cursor pointers are not claimed equivalent.
