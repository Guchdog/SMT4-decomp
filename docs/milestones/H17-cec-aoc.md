# Milestone H17: StreetPass (DDS / CEC) y Contenido Descargable (AOC / DLC)

## Scope & Architectural Summary
Reconstruct and verify readable, editable C++ for 8 critical subsystems covering Camp CEC edit work validation, card data copy, setting flag query, AOC result readiness, applet state flags, result copy value, global buffer release, and icon structure initialization.

## Subsystems Implemented & Verified
1. `CampCec_HasEditWork` (`0x001FFADC`, 24 B window, 24 B compiled, +0 B headroom)
2. `CampCec_CopyCardData` (`0x001FF814`, 28 B window, 28 B compiled, +0 B headroom)
3. `Aoc_ResultIsReady` (`0x002A17C0`, 20 B window, 20 B compiled, +0 B headroom)
4. `AocApplet_IsFlag10000` (`0x002A17D4`, 16 B window, 16 B compiled, +0 B headroom)
5. `Aoc_ResultCopyValue` (`0x002A17E4`, 24 B window, 20 B compiled, +4 B headroom)
6. `Aoc_ReleaseGlobal` (`0x002B2520`, 16 B window, 12 B compiled, +4 B headroom)
7. `CampCec_GetWorkHandle` (`0x002D73F4`, 28 B window, 28 B compiled, +0 B headroom)
8. `AocIcon_Init` (`0x0038C248`, 28 B window, 28 B compiled, +0 B headroom)

## Staged Binary Artifacts
- **Cumulative Binary:** `code.h17-final.bin` (SHA256: `8940a2a0571096fa38f7ddb1685d1ae94ebfa3da8e338acb0363df0df8e1760d`)
- **LayeredFS IPS Patch:** `code.h17-final.ips` (SHA256: `8204a6c9e3603a16207bbaf34a007b4380f3b2b80d09f7d8dcf7a2ca1e20fc28`, 30738 B)
- **Roundtrip Verification:** `apply_ips(code.bin, code.h17-final.ips) == code.h17-final.bin` passed.
