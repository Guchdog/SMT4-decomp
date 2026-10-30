# H2 APT Utility-4 runtime entry probe: corrected rerun

## Result

The corrected paired run **passed its bounded runtime contract**. The reviewed H2 base and the same image with the experimental 40-byte APT Utility-4 body both reached the live entry `0x002C0EFC`, then the original wrapper `0x002B5A1C`. Both supplied arguments `(4, 0, 0, 0, 0, 0)`, `LR=0x002C0F20`, and aligned `SP=0x0FFFFEF0`. The actual 44 bytes read at the entry are now persisted as hex and SHA-256 in the runtime report.

The prior run-003 report left the wrapper breakpoint marked `cleared=false` before sending `z0`. The runner now updates that field only after the helper returns from an acknowledged `OK`; both rerun captures report `cleared=true` and `clear_acknowledged=true`. It also stores the actual 44-byte runtime span and its hash.

## Paired captures

| Image | Entry PC / LR | Wrapper PC / LR | Arguments | SP | Runtime bytes | Wrapper breakpoint | Cleanup |
|---|---|---|---|---|---|---|---|
| reviewed_h2_base | `0x002c0efc` / `0x00103e84` | `0x002b5a1c` / `0x002c0f20` | `0x00000004, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000` | `0x0ffffef0` | 44 bytes, SHA-256 `b9a39d87d00611a2803ab486d556fca74afbae3c52a3294e98569550151f9a55` | True (acknowledged) | True / `None` |
| h2_base_plus_apt_candidate | `0x002c0efc` / `0x00103e84` | `0x002b5a1c` / `0x002c0f20` | `0x00000004, 0x00000000, 0x00000000, 0x00000000, 0x00000000, 0x00000000` | `0x0ffffef0` | 44 bytes, SHA-256 `24df48386fd274d2f96593370f951f634f412028fa517e0017db3860760daa1c` | True (acknowledged) | True / `None` |

Both children were terminated by the bounded supervisor after capture (exit code 1); no listener remained. This is not a clean emulator shutdown. Ports were `62182` and `62183`, each bound only to `127.0.0.1` and owned by the corresponding child PID.

## Frozen execution sources

The runner hashed the probe and every declared project-local direct/transitive Python helper before and after the pair. The maps were identical (9 files), and the report’s `execution_sources_unchanged` is true.

| File | SHA-256 |
|---|---|
| `tools/h2_apt_utility4_inplace_runtime_probe.py` | `80b6fd743b5f1921de8a21209f97222bd6ba676e2d666199deb7673db4dc0e0f` |
| `tools/h2_apt_utility4_caller_probe.py` | `e138aacfe8cd10e7be00117b462baa6274a33ef0f66495ff9db6612e24365679` |
| `tools/h2_autonomous_gdb_verify.py` | `c9d37b76a8f3edfe56d8dc0a6706ea0c2cf2461d491d814cc9737fb994fad8b3` |
| `tools/h2_azahar_rsp_probe.py` | `9d70a15ddd62ff6eedeccc9de54b88da7f2ec1bcda11de236c23ff64931a132b` |
| `tools/h2_calc_code_patch.py` | `bd081273d113c620e73cf9bd94d0a0dec765b5bcb4cb7a5856afa9ead5e3a525` |
| `tools/h2_calc_experiment.py` | `f70429ef3cb9e186bb5d78863aade9e1d8e4a4262108bba33c48c334b8b71aac` |
| `tools/asm_diff.py` | `9c5c7fa62c4474cfff6f78b1e60b93b703d6a1cc40bfe93e9d5ddbb587dae7bf` |
| `tools/build_check.py` | `07e4b94c423d732973aa53d4cc2cb46bbc4a2342cda8e9120e6bd09b00e70645` |
| `tools/semantic_experiment.py` | `bd55023d36f09900aed39e43512d6d9e9d4f6b6e97aade7fad8bf33a22c54277` |

The run also revalidated six offline gates before launch: direct ARM differential, original caller composition, composed H2 caller composition, observed caller context, ARM/Thumb interworking scan, and independent IPS package review. Their exact paths/hashes are preserved in `offline-gate-attestation.json`. Four inherited source-identity mismatches remain recorded in the reviewed H2 base (three mapper rows and FillPair).

## Save and runtime isolation

The user save path was hash-checked but not passed to Azahar. Its SHA-256 before/after was `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`. The disposable fixture had the same pinned hash before/after and the per-profile staged copies were unchanged. The run used separate disposable profiles, temporary RSP software breakpoints, no logical input, and no explicit `M`/`P`/`X` writes. The loopback listeners were gone after cleanup.

## Reproduction

~~~powershell
python -B -m pytest -p no:cacheprovider -q tests/test_h2_apt_utility4_inplace_runtime_probe.py
python -B tools/h2_apt_utility4_inplace_runtime_probe.py --output-dir build/agent-work/H2-semantic/h2-apt-utility4-runtime-probe-correction/run-001/runtime --base-port 62182 --startup-timeout 45 --capture-timeout 45
~~~

Focused result: **6 passed**. The runtime command exited `0`; report status is `captured_bounded_runtime_contract`.

## Limits

- The probe stops at the original wrapper entry before its body/SVC. It does not capture the service result, side effects, wrapper return, or caller continuation.
- This samples the observed ARM caller path only; indirect and alternate-state callers remain outside the scan claim.
- A separate broad TitleConfig paired runner still has a documented original-side `WM_CLOSE` timeout before the candidate side; that run does not invalidate this entry-only pair and does not establish full H2 behavior, clean shutdown, or restart persistence.
- The candidate remains experimental. H2 TitleConfig remains open; there is no source-ledger promotion or whole-game equivalence claim.
