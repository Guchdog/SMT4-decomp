# H12 Batch Integration Record

- **Base Image:** `build/agent-work/H11-semantic/h11-integrated-stage/code.h11-final.bin` (`0520e88c5fb70e16e8c5071d097fb6d3de3c9c55e57aaef8d59fbbe998a9d843`)
- **Composed Binary:** `build/agent-work/H12-semantic/h12-integrated-stage/code.h12-final.bin` (`2ce98e10b4ac2dbefd16b7d98aab04298e56461d3dbc3c1b51781e7f80fd21d7`)
- **LayeredFS IPS Patch:** `build/agent-work/H12-semantic/h12-integrated-stage/code.h12-final.ips` (`1f597c3fd6ec2ce717294b5c5063701801c92bbb5f98602e79fda55aae1309e0`, 30,001 bytes)
- **Round-Trip Fidelity:** `apply_ips(code.bin, code.h12-final.ips) == code.h12-final.bin` PASSED.
