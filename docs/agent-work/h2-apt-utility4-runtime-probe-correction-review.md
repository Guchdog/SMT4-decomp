# Independent review: corrected H2 APT Utility-4 runtime probe

## Result

The corrected run supports the stated **bounded entry-to-wrapper runtime contract**. The reviewer independently verified the retained 44-byte spans against the selected images, the acknowledged wrapper-breakpoint removal, the nine execution-source hashes, six pinned offline-gate reports, package/image identities, loopback ownership, and termination/listener records. This does not verify APT service behavior or complete H2. Keep the candidate experimental and H2 open.

This was a read-only review. I did not launch Azahar, run tests/builds, or open/hash the protected user save. I independently checked 31 declared non-save inputs; all match their packet pins. The declared `build/h3-fixture/source/sdds4game1.sav` was not independently opened/hashed. The handoff checker below checks that disposable fixture as a packet input; it does not access the protected user-save path.

## Runtime bytes and dispatch

At image offset `0x1C0EFC` (runtime PC `0x002C0EFC`, image base `0x00100000`), the report retains 44 bytes for each side. I decoded the report hex, checked its length/hash, and compared it to the corresponding pinned image slice:

| Side | Runtime entry bytes (44 B) | SHA-256 | Exact image-slice match |
|---|---|---|---|
| Reviewed H2 base | `0010a0e304e02de50cd04de20400a0e30130a0e10120a0e100108de504108de5bed2ffeb0cd08de204f09de4` | `b9a39d87d00611a2803ab486d556fca74afbae3c52a3294e98569550151f9a55` | yes |
| Base + APT candidate | `004e2de90000a0e300008de504008de50400a0e30010a0e30020a0e30030a0e3bed2ffeb0c88bde804f09de4` | `24df48386fd274d2f96593370f951f634f412028fa517e0017db3860760daa1c` | yes |

Both captures report entry `PC=0x002C0EFC`, `LR=0x00103E84`, then original wrapper `PC=0x002B5A1C`, `LR=0x002C0F20`, arguments `(4,0,0,0,0,0)`, `SP=0x0FFFFEF0` (`SP & 7 == 0`), and two zero stack words. The wrapper stop is before its body. The candidate changes 29 bytes within the 40-byte candidate body.

The corrected runner calls `rsp_clear_bp(rsp, WRAPPER)` and only then `mark_software_breakpoint_cleared`. The helper requires an `OK` reply from `z0`; otherwise it raises and the capture becomes partial. Both reports now have `cleared=true` and `clear_acknowledged=true`. The focused test exercises the marking helper and unknown-address rejection, but not an injected failed `z0`; I did not rerun tests.

## Source, offline-gate, and package identities

The nine `execution_source_hashes_before` and `execution_source_hashes_after` entries are identical. I recomputed each current source hash; all nine match both maps:

| Execution source | SHA-256 |
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

All six offline gate report hashes match their attestation and packet pins: direct differential, original caller composition, composed-H2 caller composition, observed caller context, ARM/Thumb scan, and independent IPS package review. The first four report `passed=true` with no failures; the ARM scan records seven ARM hits and zero Thumb hits; the package audit records exact round-trip, 29 added bytes, and four inherited source-identity mismatches.

The base image, base IPS, candidate image, candidate IPS, candidate C++ source, and package manifest hashes match the run's attestation/manifest. The candidate source hash is `1f7228e30cfdb3c14497f96fdce3bc65845ad65bb4b3b5491c5ab2b382742e06`. The four inherited base source mismatches remain (three mapper entries and FillPair). The manifest kind still reads `experimental offline H2 image; not runtime-verified or promoted`. “Not promoted” remains correct; “not runtime-verified” should be understood as no semantic/service-level verification. This new run verified dispatch only up to the wrapper. No manifest edit was made.

## Loopback, cleanup, and save evidence

The listeners are recorded as `127.0.0.1:62182` / PID `11816` and `127.0.0.1:62183` / PID `9456`; each PID matches the launched host process. Both processes were detached, terminated by the bounded supervisor, and have `listener_after_cleanup: null`. Exit code `1` is the recorded bounded termination result, not a guest crash or clean Azahar shutdown. The report also records title ID and code-patch application for both profiles.

The runner's command passes the staged Azahar executable, GDB port, and CCI; it does not pass the protected user-save path. The source code hash-checks that path, stages a copy of the pinned build fixture in each isolated profile, and compares the staged/fixture hashes before and after. The report records equal before/after source-save hashes, equal fixture hashes, and `source_save_used_as_emulator_input=false`. Those are report/code claims; I did not independently access either save file. The stage field `profile_seed_contains_save=false` is a literal in the runner, not a saved recursive-inventory result.

The probe uses software breakpoints, register/memory reads, and no logical input. The code sends no explicit `M`, `P`, or `X` packets. This wording does not imply that software-breakpoint insertion has no transient code-memory effect.

## Scope and remaining limits

The independent review supports only the observed ARM entry-to-wrapper dispatch and ABI snapshot. It does not observe the wrapper/SVC body, result, service effects, caller continuation, full TitleConfig behavior, clean shutdown, or restart persistence. The separate broad `WM_CLOSE` timeout remains unresolved. The candidate is not promoted, H2 remains open, and this is not whole-game equivalence.

The upstream handoff records six focused tests passed and a successful runtime command; neither tests nor Azahar were rerun here. The stale manifest wording is a non-blocking label issue, not evidence of semantic correctness.
