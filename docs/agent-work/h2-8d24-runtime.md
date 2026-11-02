# H2 runtime comparison after `0x002B8D24` conversion

The private loopback-bound Azahar verifier ran original and patched profiles with the same scripted Audio Settings inputs. The patched image was composed from the reviewed H2 image `acd8b2f35df08f225ca65b0fbf8aeef2dbbaa71171904e31c301e8bff6a51446` plus the 360-byte `0x002B8D24` production slot. Original-based IPS replay passed.

- Runtime report: `build/h2-8d24-integration/runtime-run/autonomous-gdb-verification.json` (SHA-256 `629e049abf67a224ac32da67a2b947530602335ccd11ec4e04d54647f6d4a22f`).
- Paired scripted behavior: passed; 51 scripted actions and 19/19 checkpoint comparisons matched, including `g_ConfigBytes` and normalized `TitleConfigWork`.
- Final image SHA-256: `f87b3149c03a58cc16eb3e903f0102b6f7ce47fdb3523740e992c3824f94e940`.
- Original-based IPS SHA-256: `53f5da5aa13cdb6acfa2aa22ab3a8315fb103affb94cbbfc56f127b3019fbbc7`.
- The verifier does not instrument `0x002B8D24`; whether this helper was reached on either side is unverified. The paired result applies to the exact cumulative image and scripted path, not function-specific execution. The report explicitly does not support full H2 acceptance: readiness and same-session re-entry did not complete on either side; physical input mapping and scheduling are unproven. Restart-state/persistence outcomes matched, but the controlled lifecycle did not complete.

The runner was `tools/h2_autonomous_gdb_verify.py` SHA-256 `c68c357d36ed7ab6b45b7f63bfec0ebd8ae8578b68ab2f0d1588cd89c419a94e`. The base image report notes source identity mismatches for some mapper and FillPair translation units. This comparison therefore supports parity for the exact pinned image artifacts and scripted scenario, not a claim that the entire current source tree produced that base image or that H2 is closed.
