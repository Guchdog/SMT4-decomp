# H2 `0x0029F278` production conversion — run006

## Result

The complete cursor updater now has typed C++ in `src/engine/leaf_batch46_b.cpp`.
The standalone pinned-image builder compiles the production TU, resolves 15 ARM
calls to the pinned helper entries, places the local four-byte `.rodata.cst4`
mask table after the function body, and redirects only the original entry. The
body is 1024 bytes; code plus table is 1028 bytes. The original 1536-byte span
after the entry remains byte-identical. A word-aligned image scan found no
external direct branches or aligned absolute pointers into the original body.

Run006 passed 144/144 direct cases, three compositions through the original
`TitleConfig_Calc` state-1 caller, and a wrong-target sensitivity control. The
direct cases compare return/fault/stop state, `r4-r11` and SP, the full cursor,
input globals and counters, helper call/argument order, and ordered non-stack
writes. The three caller cases execute the real updater and direct binary
helpers but keep the existing Calc runner's outer service boundaries modeled.

| Evidence | Result |
|---|---:|
| Original image SHA-256 | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Patched image SHA-256 | `bb1e15d013e4a905cb3288a28029f15329b7a38be1b0e0835171136d07127c36` |
| Production source SHA-256 | `545cf3882ffe52d3f2a8346613ef546fe7a56d5835726d64d2f3923f1e54481a` |
| Production object SHA-256 | `927303525e167023ae1e784f15fb956face54d9e1d8903abd4ac3faeab7485f4` |
| Placed body SHA-256 / size | `8816683aa169fbc8ccedb162617f02190f96e2ed5e0d0750272a2208b51101e4` / 1024 bytes |
| `.rodata.cst4` bytes | `08040102` at `0x003FEA24` |
| IPS SHA-256 | `9933b58a513653348d71a5a55332bad08bacb194bc64350245b1d30334b32fea` |
| Direct / caller cases | 144 / 3 |
| Wrong-target control | detected |
| Run006 report SHA-256 | `e75bdc02ff6bcba773624aee7b9079d7d91f2a21ce8808b90046f696a9a31271` |
| Runtime | not run |

Reproduce into a new output directory:

```powershell
python tools/h2_29f278_production_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-0029f278-production/<new-run> --seed 20261102 --samples 128
```

## Scope and limits

All direct helper implementations remain pinned original code. Fixtures use
synthetic valid RAM and cover observed cursor fields and bounded logical input
IDs; they do not establish physical controls or natural event scheduling. The
caller comparisons use original `TitleConfig_Calc` with its unrelated outer
service boundaries modeled. Incidental restored-stack bytes and discarded read
ordering are not compared. The accumulator's text-tail cave is shared with this
standalone layout, so this patch is not merged into the accumulated H2 image.
No runtime or whole-game equivalence is claimed.
