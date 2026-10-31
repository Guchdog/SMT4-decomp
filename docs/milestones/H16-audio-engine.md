# Milestone H16: Subsistema de Audio, Voces y Video / Mobiclip

## Scope & Architectural Summary
Reconstruct and verify readable, editable C++ for 8 critical sound engine subsystems covering sound buffer assignment, buffer size calculation from sample rate and channels, secondary buffer assignment, data size computation with word alignment, sample byte calculation from sample count, data base address derivation, data element count retrieval, and active sound ID update in global sound context.

## Subsystems Implemented & Verified
1. `AsdSoundEffect_SetBuffer` (`0x00110C2C`, 24 B window, 24 B compiled, +0 B headroom)
2. `AsdSoundEffect_GetBufferSize` (`0x00110C44`, 28 B window, 28 B compiled, +0 B headroom)
3. `AsdSoundEffect2_SetBuffer` (`0x00121150`, 24 B window, 24 B compiled, +0 B headroom)
4. `AsdSound_GetDataSize` (`0x00121F20`, 32 B window, 24 B compiled, +8 B headroom)
5. `AsdSound_GetSampleBytes` (`0x00122094`, 48 B window, 44 B compiled, +4 B headroom)
6. `AsdData_GetBase` (`0x00128F34`, 16 B window, 16 B compiled, +0 B headroom)
7. `AsdData_GetCount` (`0x00128F44`, 20 B window, 16 B compiled, +4 B headroom)
8. `StatusDown_SetActiveSoundId` (`0x00215A44`, 28 B window, 28 B compiled, +0 B headroom)

## Staged Binary Artifacts
- **Cumulative Binary:** `code.h16-final.bin` (SHA256: `012ce664c01d605b6ecdf7fd9be515f99a5492f38795270e5d1677e9acb6cd2c`)
- **LayeredFS IPS Patch:** `code.h16-final.ips` (SHA256: `a539b0ed10b5a7495915d0a0095133375eff94cb443cde02120dc45e174d5e30`, 30589 B)
- **Roundtrip Verification:** `apply_ips(code.bin, code.h16-final.ips) == code.h16-final.bin` passed.
