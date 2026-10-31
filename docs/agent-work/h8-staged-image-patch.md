# H8 Staged Composite Image and Patch Report

- **Base Image:** `build/agent-work/H7-semantic/h7-integrated-stage/code.h7-final.bin`
  - SHA-256: `477ae5941b1163f56533b74128635e6deb22ddf796d4f4c18d65bdb02ddda3f8`
- **Output Binary:** `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.bin`
  - SHA-256: `bddb53a22a86d9759eb138164ddbc6652f00e5066446c2ef6c85c3a6bb8e3b6d`
- **Mod IPS Patch:** `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.ips`
  - SHA-256: `dc766de6633d771d9ce206d324a864ce61e26722e4d2d4715c1be3587b08f091` (21,362 bytes)
  - Round-trip IPS verification: **PASSED**
- **Reconstruction Metrics:**
  - Candidates: 8 functions
  - Original Window Footprint: 4,080 bytes
  - Reconstructed C++ Size: 2,472 bytes
  - Total Headroom Margin: +1,608 bytes (zero overflow anywhere)
