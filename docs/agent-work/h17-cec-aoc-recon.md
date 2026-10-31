# H17 StreetPass (DDS / CEC) and DLC (AOC) Architecture Reconnaissance Record

- **Milestone:** H17 (StreetPass / CEC and DLC / AOC / StreetPass / CEC y Contenido Descargable / AOC)
- **Scope:** Reconstruct and verify readable, editable C++ for 8 critical subsystems covering Camp CEC edit work validation, card data copy, setting flag query, AOC result readiness, applet state flags, result copy value, global buffer release, and icon structure initialization.
- **Offline-First Differential Gate:** Passed with 100% register/memory parity across all 8 subsystems on Unicorn ARM11 engine.
- **Binary Footprint:** 176 B compiled out of 184 B original window (+8 B headroom).
