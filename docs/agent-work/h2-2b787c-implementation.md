# `0x002B787C` implementation and offline evidence

## Result

`AsdText_GetLineCount` has a typed C++ production body in
`src/engine/leaf_batch42_c.cpp`, and `src/ui/status_down.cpp` binds its local
declaration to `engine_func_002b787c`. Its original 176-byte slot is fully
occupied. The converted body retains both unresolved original callees. The
ledger now says `non_matching`, because the compiled code is not byte-identical
to the reference.

## Input and artifact identities

- Pinned `code.bin`: SHA-256
  `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`.
- Candidate runner report:
  `build/agent-work/H2-semantic/h2-asdtext-line-count-convert/run003/offline-report.json`,
  SHA-256 `3e56cf5936abf139c2ce29e0c9b9b6a897419a638a1de3a47cf99bb601dc50e1`.
- Staged production image: SHA-256
  `a915d0baee331366636fd9e25d55bfafa3554351f15d242fce3f52f9675d1dec`.
- IPS: SHA-256
  `a501c4b078961d69ac720f252331f29380d4186dfebe1ec333902891e57896c2`.
- Final-address production offline report:
  `build/h2-2b787c-integration/staged-validation/production-offline-validation.json`,
  SHA-256 `5bd5fb164d65dabd4d3e00960b83d1a3f06540c5d7833f4ebfbe3f64e2308ee7`.
- Paired autonomous runtime report:
  `build/h2-2b787c-integration/runtime-probe-001/autonomous-gdb-verification.json`,
  SHA-256 `d57694f1200057a377d97bb9a66eb8d36aea0ed81dde20caa20bf2b5c444494e`.
- Cumulative runtime manifest SHA-256:
  `f9e00762835b87434e67c47c959dddced98a764ea47a29ae52dec8ed46877690`.
- Production function body: 176 bytes; body SHA-256 is recorded in
  `build/h2-2b787c-integration/staged-image/manifest.json`.

## Commands and outcomes

| Command | Result |
|---|---|
| `python tools/h2_2b787c_experiment.py` | Exit 0; 515 direct cases, selector 11/19 caller compositions, six negative controls; body 176/176 bytes. Both the direct signed-bound case and its mutation control use an isolated initialized record table, a count control at offset 1, and a sentinel at offset 998. |
| `python tools/h2_2b787c_staged_image_patch.py` | Exit 0; two `R_ARM_CALL` relocations target even ARM addresses; one-slot IPS round trip passed. |
| `python tools/h2_2b787c_staged_validation.py` | Exit 0; 515 direct cases and both selectors passed at final address `0x002B787C`. |
| `python tools/build_check.py --out-dir build/h2-2b787c-integration/full-build -j 4` | Exit 0; 204/204 ARMv6K translation units compiled. |
| `python tools/h2_2b787c_runtime_verify.py --output-dir build/h2-2b787c-integration/runtime-probe-001 --base-port 60126 --startup-timeout 60 --packet-timeout 240` | Exit 0; 19/19 H2 checkpoints matched; GDB directly invoked the guest function once in each profile, both returned and probe-consumed `1`, with SP restored. |
| `python tools/progress.py --write` | Exit 1 on unrelated existing `script_vm_func_001ea928` source in `src/engine/leaf_batch46_b.cpp`; the progress parser could not parse that body. |

The differential checks compare returned register/fault behavior, callee-saved
registers and SP, direct-callee entry order/arguments/returns, relevant input
memory, and non-stack writes. The original direct callees execute from the
pinned image. Six mutation controls for sentinel, count/stop/payload handling,
mapping delta, and signed bound were detected.

## Limits and next step

Fixtures use initialized mapped handles/tables and reachable sentinels. The
caller compositions execute original `0x00286928`, with deterministic hooks for
its other services. They do not establish runtime selector frequency or the
semantic names of table deltas. The two other direct callers are statically
audited but not executed. Null/malformed/sentinelless inputs, concurrency,
MMIO aliasing, and unbounded arithmetic domains are unresolved.

The runtime report uses the existing H2 scenario and adds a controlled direct
guest invocation at its paused Calc checkpoint. The normal H2 callback route
passes selector 6 and did not naturally reach this helper; the direct GDB call
does not establish natural caller reachability. Next: independent review of the
runtime probe and final integration, then commit/push this bounded conversion.
H2 readiness, same-session re-entry, and overall H2 equivalence remain open.
