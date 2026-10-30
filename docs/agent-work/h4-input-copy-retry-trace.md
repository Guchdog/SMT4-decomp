# H4 stable input-copy commit capture

## Result

The paired original/H3-patched runs both reached the stable commit at `0x0012A8DC` after the runner removed its helper-entry breakpoint and let the target retry loop run without per-attempt stops. At that boundary, the live effective count in `r4` was 1 in original and 2 in patched, and the selected record count in `sb` was 1 in both. The source object pointer saved in the helper frame was `0x10000000`; the destination pointer was `0x004E3C28`.

The pinned ARM code at `0x0012A83C..0x0012A858` computes the first source slot from `(r4 - i + 8) remainder 8`, with the first loop index `i=0`. The runtime values are within the observed 0..7 domain, so the successful attempt's selected indices derive as 1 original and 2 patched. The corresponding slot bases are `0x10000010` and `0x10000020`, and the payload spans begin at `0x10000038` and `0x10000048`. Each derived payload read passed the broad RSP address guard and fell inside the captured 0x100-byte source object span. These indices are derived from live commit registers plus the pinned instruction sequence; the successful attempt's `r3` at the load was not captured directly.

At the stable-commit breakpoint, both 16-byte reads from the derived source payload addresses and both destination records were zero. The source payload reads happen after the helper has passed its consistency comparisons and branched to `0x0012A8DC`; they are not reads at the successful attempt's payload load. The recorded source header's `+0x10` value at that post-branch boundary is 5 original and 6 patched, while live `r4` is 1 and 2. This may reflect a later source update and does not show that the source remained unchanged through the debugger read. The destination at the same boundary is stronger evidence of the bytes already copied. After the helper returned, the caller-local result word at `[SP+8]` was 1 on both sides; the destination and the separately captured post-`0x00128610` output were also zero. This confirms a one-record stable fallthrough and the selected index derived from the live commit registers and pinned instructions, but does not establish that the source bytes read after the branch were the bytes loaded during that pass. No active physical input or nonzero sample was observed.

## Capture and offline gates

The runner's checkpoint setup uses controlled GDB writes to the title state, temporary logical input-getter stubs, and registers. The copy-call samples themselves are passive reads. No physical/front-end input or axis data was injected, and the source save was not accessed by the review worker or modified by the runtime runner.

Before the paired runtime run, all required offline-first gates passed:

- H3 final placement and ARM/Thumb interworking: passed; IPS round-trip true; final image SHA-256 `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`.
- H3 title-load differential: passed with its negative control detected.
- H3 caller composition: passed.
- H4 direct reader differential: 119 cases, zero differences, negative control detected.
- H4 camera composition: six cases, mutation control detected.

The H3 title/H4 helper offline reports are under `build/agent-work/H4-semantic/h4-input-copy-retry-trace/run-002/checks/` and are hash-pinned in the task handoff.

## Paired runtime behavior and integrity

The paired report status is `observed`. Both runs reached the field manager and completed 250 field ticks. Title-entry registers, title-state-8 bytes, save/load callback snapshots, post-confirm progress, the bounded field-scene signature, and tick counts compared equal. `post_confirm_events_equal` was false; that event-stream difference remains unresolved. This is checkpoint evidence, not H4 or whole-game equivalence.

The caller and transform probes hit on both sides. The staged save hash was unchanged within each run, the non-mod user-profile manifest was unchanged within each run, and the Azahar processes exited after the runner. The original and patched profile roots are not claimed as identical starting baselines. The external source save remains 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` after the run.

## Retry-loop limits

A separate per-attempt trace stopped at every payload and stability boundary. Its 2,048-event external ceiling recorded 682 completed retry edges and stopped during the next payload attempt in both processes. The caller later returned result count 1 after the trace breakpoints were cleared. This high-interruption trace did not capture a commit and is not used to estimate a retry bound.

The successful paired capture used only one internal breakpoint at `0x0012A8DC`, allowing the helper's consistency loop to run between the entry and commit. The target loop has no internal retry limit. This run does not count retries or establish a maximum time to commit; the RSP wait remains externally bounded. No source producer/thread, physical input mapping, player movement, interaction, or zone transition is identified.

## Reproduction and frozen identities

The paired run command was:

```powershell
python tools/h3_autonomous_verify.py --output build/agent-work/H4-semantic/h4-input-copy-retry-trace/run-002/checks/runtime-stable-commit-001 --profile-root E:/SMT4decomp/build/agent-work/H3-semantic/h3-runtime-isolated-run-042 --callbacks 250 --timeout 90 --confirm-load --post-callbacks 60 --field-ticks 250 --input-copy-stable-commit --field-probe-address 0x0011c640 --field-probe-address 0x0012a758 --field-probe-address 0x0011c644 --field-probe-address 0x0011c66c
```

Runner SHA-256: `927a16db9be87db17edaf6fc2ce3d755742c2fbff8f83a5ea9c7e195c4db6dc3`.

- `report.json`: `93a97a696fd324248c1948606e51e03554161696052862d717fd694da7956348`
- `original.json`: `b62fedceb72cb5ec5cc941a201f73d1ec9e41e9dff09bfcaa2f2e6a6c8f52bcc`
- `patched.json`: `f860714b7ed603978ad3eef56b3bc09589888ef5cdfab0d636f5bb12d2d96a6f`
- High-interruption original trace sidecar: `83056fb9c9ec0f1de076f24363de8365073c0d9a340724a448634b25188253da`
- High-interruption patched trace sidecar: `6bec38a3824a8320dd065829a5c33de49844d8de48ec7b4b2e8908b79473694c`

