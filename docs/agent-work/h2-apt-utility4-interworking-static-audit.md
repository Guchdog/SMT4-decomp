# H2 APT utility-4: ARM/Thumb immediate-call scan

On the pinned original image (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), an aligned ARM B/BL scan across configured actual text `[0x00100000,0x003FE624)` finds seven immediate direct callers of `0x002C0EFC`: three `BL` sites (`0x002C0F6C`, `0x002C1260`, `0x002C1304`) and four unconditional tail `B` sites (`0x00106F00`, `0x0010700C`, `0x002A8164`, `0x002C5638`). All are in ARM state and target the aligned ARM entry. The exact instruction words are preserved in `build/agent-work/H2-semantic/h2-apt-utility4-interworking-static-audit/run-001/scan.json`.

A separate raw halfword scan examined every possible 2-byte offset in that same text span for Thumb-2 immediate `BL` and `BLX` encodings whose decoded target is `0x002C0EFC`; it found none. This is evidence against an immediate direct Thumb caller in the scanned span. It cannot rule out indirect/computed calls, alternative mixed-state paths, or references outside the configured text region, and pattern scans can encounter data.

The candidate's resolved `R_ARM_CALL` is an ARM `BL` at `0x002C0F1C` to original ARM wrapper `0x002B5A1C`. The observed caller at `0x00103E80` is ARM `BL` to bridge `0x002C5624`, which uses ARM `B` at `0x002C5638` to reach the candidate while preserving LR `0x00103E84`. Offline hooks observed ARM state on tested paths, but there is no exhaustive runtime proof of every incoming edge. No emulator launch was performed.

This narrows the direct-call state domain for this entry, but does not complete interworking validation for indirect callers or the H2 runtime scenario. See the scan JSON for byte ranges, method, decoded hits and limitations.
