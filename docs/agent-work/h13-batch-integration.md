# H13 Batch Integration Record

- **Base Image:** `build/agent-work/H12-semantic/h12-integrated-stage/code.h12-final.bin` (`2ce98e10b4ac2dbefd16b7d98aab04298e56461d3dbc3c1b51781e7f80fd21d7`)
- **Composed Binary:** `build/agent-work/H13-semantic/h13-integrated-stage/code.h13-final.bin` (`e99fd3b5d3a1977e5a223ab55079dbcef7a97ae9fac7635a002e40078b066976`)
- **LayeredFS IPS Patch:** `build/agent-work/H13-semantic/h13-integrated-stage/code.h13-final.ips` (`f88b31696a1754b70a3816527b207f5a6eeb4c57a4b55ecc7300a04c965ddd5a`, 30,184 bytes)
- **Round-Trip Fidelity:** `apply_ips(code.bin, code.h13-final.ips) == code.h13-final.bin` PASSED.
