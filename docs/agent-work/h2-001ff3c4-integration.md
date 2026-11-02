# `0x001FF3C4` offline conversion integration — run006

## Result

The full axis mover was translated to typed C++ in `src/engine/leaf_batch43_a.cpp`. Clang emits a 580-byte main function and outlines two local helpers (152 and 148 bytes). The integrator reconstructs the contiguous 880-byte sequence at the original entry; it fits the original 1,104-byte slot. The main function has ten `R_ARM_CALL` relocations to pinned `ui_func_00254ca8`; both outlined helpers have no relocations.

The direct original-versus-candidate run passed 162/162 cases. It compares the full 0x28-byte record, return, error/stop state, saved registers and SP, ordered helper arguments/results, and ordered record writes. Fixtures cover all primary/fallback families, query precedence and simultaneous results, flags, signed/high-bit values, wrapped sums, C branch counts 0/1 and width greater than count, and the B branch `SUBS` overflow case. Four compositions through the real `TitleConfig_Calc` slice passed with the original query-service chain: stable cursor, active cursor/no input, logical bits, and the initialized H2 cursor. A deliberately wrong first query target was detected.

The two recovered contract corrections are reflected in both implementation and cases: `C2/C1` has no `count <= 1` gate and compares/advances with original width while clamping reset values; `B0/B2` uses the N bit after wrapped `SUBS offset,#1`.

| Evidence | Result |
|---|---:|
| Pinned original image SHA-256 | `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558` |
| Candidate source SHA-256 | `c2416b153b0ec2b1c91b6a8703e3f5c0a325e350c42bf3099c64f36ea8779cc7` |
| Candidate object SHA-256 | `29346e7b35333bbb4dbb9d0f662225aeda68194b393336f6b66a8e2333d531ae` |
| Integrated 880-byte sequence SHA-256 | `44c6adab3101df0623cdeeea1b69459c41c7d0bfb4c8f12bd9fe62db9dd04717` |
| Runner SHA-256 | `7d6d1931c9b29bb6fd0521f1b74d0ddd187e875371b9d71dc5c4cf9d56a05d35` |
| Run report SHA-256 | `3cfbe478a01b5753cf50bb392c9627e9cf22c6687a4c35e175c907328d8de3a9` |
| Direct / caller results | 162/162; 4/4 |
| Wrong query-target control | detected |
| ARMv6K full build | 204/204 translation units, `build/h2-1ff3c4-full` |
| Runtime | not run |

Reproduce in a fresh ignored output directory:

```powershell
python tools/h2_1ff3c4_experiment.py --output build/h2-1ff3c4-direct/<fresh-run> --seed 20261109 --samples 112
python tools/build_check.py --out-dir build/h2-1ff3c4-full --jobs 4
```

## Limits

The direct differential replaces the query service with the same deterministic ten-result sequence on both sides. Caller compositions retain the original query/input/calibration chain but model unrelated outer Calc services. These fixtures do not prove physical controls, input timing, natural H2 scheduling, runtime sound, or whole-game behavior. Valid aligned ordinary RAM is assumed; MMIO, concurrent mutation, malformed pointers, and exact fault/read ordering are not claimed. Independent review is pending.
