# H2 `0x002C615C` production integration — run004

## Result

The production symbol `ui_func_002c615c(u32,u32)` is readable C++ with a
`u64` ARM return: quotient in `r0`, remainder in `r1`. Its compiled body is
164 bytes with no relocations. The builder places it at `0x003FE624` and
redirects only the original entry with an unconditional ARM `B`. The patch
leaves the rest of the original 556-byte body intact.

That suffix must remain because six direct branches from the adjacent pinned
`0x002C6C10` helper enter division labels at `0x002C6190`, `0x002C61B8`,
`0x002C61E8`, `0x002C621C`, `0x002C6240`, and `0x002C6264`. The offline census
found no aligned absolute pointers into the helper body. The IPS contains two
nonoverlapping records (the 4-byte entry and 164-byte cave body) and reapplies
to the measured image exactly.

The production-source body passes 368 direct original-versus-patched cases,
including nine zero-divisor observations, and two compositions through the
original `0x002BF9F0` preview helper. Each caller fixture reaches the division
helper twice with positive duration and keeps every other callee original. A
wrong entry target is detected.

| Evidence | Result |
| --- | ---: |
| Pinned source image SHA-256 | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Patched image SHA-256 | `5d5fc7af6a39eda53418f41add058059d940cad30450870d2685572ccbc6f221` |
| Production source SHA-256 | `427c2b44894dc27b770f431ab501a390589e40d7d010547d4976fee269769697` |
| Production object SHA-256 | `778a6e0259ae83d34f1da7eefc9b51ebbeabef62ddbfb13d83155fdb8ab23b07` |
| Helper body SHA-256 / size | `d98896af49e2177a7afea432b3f88daa517652ea0e22e086b6c514928dc12c71` / 164 bytes |
| IPS SHA-256 | `d635ba9b2f88712482feb211dda30a8fceb8e3ef080a6a90caccfe955c953519` |
| Direct / original-caller cases | 368 / 2 |
| Negative control | detected |
| Runtime | not run |

Reproduce with:

```powershell
python tools/h2_2c615c_production_experiment.py --output build/agent-work/H2-semantic/h2-titleconfig-002c615c-production/<new-run> --seed 20261025 --samples 256
```

The runner pins the original image, compiles the production TU, audits the
interior branch targets and zero cave, checks the ARM branch target, rebuilds
and round-trips the IPS, compares direct register results and real caller
effects, and checks a wrong-target control.

## Scope and limits

The caller cases execute the pinned original H1 preview helper and all its
other original callees. They establish the positive-duration interpolation
domain and real `r0/r1` ABI route. The cursor updater `0x0029F278` was not run;
its call to this helper remains covered by static contract only. The
accumulated five-callback H2 image allocates the same shared text-tail cave, so
this standalone replacement is not part of that image. Runtime, invalid
pointers, concurrent or MMIO access, physical timing, save persistence, and
whole-game equivalence are not established.
