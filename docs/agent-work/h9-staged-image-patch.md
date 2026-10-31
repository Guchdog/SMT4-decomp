# H9 Staged Composite Image and Patch Report

- **Base Image:** `build/agent-work/H8-semantic/h8-integrated-stage/code.h8-final.bin`
  - SHA-256: `bddb53a22a86d9759eb138164ddbc6652f00e5066446c2ef6c85c3a6bb8e3b6d`
- **Output Binary:** `build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.bin`
  - SHA-256: `0043ccce8b7bf4a53bbe5312414b27d8c0184345cf674a7e11c1759d0af667ac`
- **Mod IPS Patch:** `build/agent-work/H9-semantic/h9-integrated-stage/code.h9-final.ips`
  - SHA-256: `975fcde2a8cbdd4b332126974af00ce2d7588517ed30bc2130c160f8968fdd20` (27,208 bytes)
  - Round-trip IPS verification: **PASSED**
- **Reconstruction Metrics:**
  - Candidates: 8 functions
  - Original Window Footprint: 4,596 bytes
  - Reconstructed C++ Size: 3,328 bytes
  - Total Headroom Margin: +1,268 bytes (zero overflow anywhere)
