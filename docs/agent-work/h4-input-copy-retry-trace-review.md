# H4 input-copy stable-commit trace: independent review

## Result

The run-002 packet's declared input hashes all match. The raw paired sidecars and pinned ARM instructions support the reported stable-branch observation and the derived first-record source indices. At `0x0012A8DC`, both runs reached the fallthrough after all three consistency comparisons; live `r4` was 1 original / 2 patched, and `sb` (`r9`) was 1 on both. The helper frame contains saved source and destination pointers `0x10000000` and `0x004E3C28`, and the saved caller result pointer is `0x0FFFFED0`.

The derived first-iteration indices are 1 and 2, using `((r4 - i + 8) signed remainder 8)` with `i=0`. This yields source-slot bases `0x10000010` and `0x10000020` and payload addresses `0x10000038` and `0x10000048`. Each 16-byte payload span is within the captured 0x100-byte source span. This is a derivation from live commit registers and the pinned instructions: the successful iteration's `r3` was not directly sampled.

The most important boundary caveat is that the `committed_source_payload` read is performed **after** the helper has branched through the stable comparisons to `0x0012A8DC`; it is not a contemporaneous read at the payload load. At that same breakpoint, the recorded destination is the stronger evidence of the bytes already copied. Both derived-source reads and both destination-at-boundary reads are zero; the caller's post-helper result count is 1 and its output is still zero, as is the later post-transform output. The post-branch source reads do not by themselves prove that source bytes remained unchanged between the copy and the debugger read.

## ARM/frame and index audit

Pinned `extracted/exefs/code.bin` SHA-256 is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Independent `tools/split_asm.py` output confirms the ARM body and call frame:

- `0x0011C5EC` initializes the two-word cursor local at its `SP+0x10/+0x14` and the second local at `SP+0x0C` to `0xFFFFFFFF`, passes their pointers at caller `[SP]`/`[SP+4]`, and passes the selected-count result pointer `SP+8` in `r3` at the call at `0x0011C640`.
- At helper entry the caller SP is `0x0FFFFEC8`. `0x0012A758` pushes 13 words, then allocates 0x14 bytes, so at the observed helper frame SP `0x0FFFFE80`, saved incoming `r0`, `r1`, and `r3` are respectively at frame `+0x14`, `+0x18`, and `+0x20`. These locations yield `0x10000000`, `0x004E3C28`, and `0x0FFFFED0`, matching the sidecar's source, destination, and result-count pointers. The caller stack arguments are at helper-frame `+0x48/+0x4C`, and the sidecars report cursor pointer `0x0FFFFED8` and second local pointer `0x0FFFFED4`.
- The copy loop computes index with `SUB r2,r4,r5`, `ADD #8`, signed quotient correction using `ASR` and `LSR #29`, `BIC #7`, and subtraction at `0x0012A83C..858`. For its first item, `r5=0`; with positive `r4=1` or `2`, signed remainder of `r4+8` by 8 is exactly 1 or 2. At the stable-branch boundary the captured `r5` is already 1 because the single record copy incremented it; the index derivation correctly uses the first iteration's `i=0`, not that post-loop register value.
- `sb=1` bounds the observed helper invocation to one selected record. The five source loads are at slot offsets `+0x28/+0x2C/+0x30/+0x34/+0x36`, with the three words and two halfwords stored to the 16-byte destination before the stability comparisons.
- At `0x0012A89C..8D8`, the helper checks source `+0x10` and both 64-bit snapshot pairs, branching to `0x0012A780` on any mismatch. Reaching `0x0012A8DC` is direct control-flow evidence that this pass fell through all comparisons. The breakpoint is at the start of the success stores: `str sb,[r1]` and cursor/count stores have not yet executed at that PC. The later caller-local count `1` at `0x0011C644` confirms successful return and result publication.

### Post-branch source header nuance

The run-002 stable-boundary sidecars read source `+0x10=5` original and `6` patched while live `r4` at the `0x0012A8DC` stop is 1 and 2. This memory read occurs after the successful comparison branch and can reflect a later source mutation; it must not be described as the unchanged snapshot that the helper compared. The target reached the stable fallthrough, but the captured header bytes do not establish that the source remained stable up to or through the debugger's subsequent payload read. No writer or mutation timing is identified here.

## Paired bytes and ranges

| Evidence | Original | Patched | Review |
|---|---|---|---|
| Helper commit PC / frame | `PC=0x0012A8DC`, `SP=0x0FFFFE80`, `r4=1`, `sb=1` | same PC/SP, `r4=2`, `sb=1` | Both have `status=stable_commit_observed`; `retry_iterations_observed=false`. |
| Saved pointers | source `0x10000000`, destination `0x004E3C28`, result local `0x0FFFFED0` | same | Matches ARM frame layout and caller. |
| Derived first source index | 1; slot `0x10000010`; payload `0x10000038` | 2; slot `0x10000020`; payload `0x10000048` | Formula is within 0..7 for these live values. These source addresses are derived, not read from `r3` at the successful load. |
| Post-branch payload read | 16 zero bytes, `range_valid=true` | 16 zero bytes, `range_valid=true` | Read at the stable-branch breakpoint after the payload copy, not at the actual load instruction. |
| Destination before helper's final count/cursor stores | `0x004E3C28`, 16 zero bytes, `range_valid=true` | same | Stronger evidence for the bytes already present after the copy and accepted comparisons. |
| Caller after helper | `[SP+8]=1`, output zero | `[SP+8]=1`, output zero | Count comes from local `0x0FFFFED0`, not an inferred return-register value. |
| Caller after transform | output zero | output zero | Separately captured at `0x0011C66C`. |

The source base's original caller-entry 0x100-byte span was validated as `[0x10000000,0x10000100)`. The computed payload ranges are `[0x10000038,0x10000048)` and `[0x10000048,0x10000058)`, wholly inside that span. The destination range is `[0x004E3C28,0x004E3C38)`. The runner's sidecar flags each of these reads `range_valid=true`; these range guards do not provide object locking or atomicity.

## Auxiliary event-limit trace

The documented high-interruption trace sidecars are present under the earlier `run-001/checks/runtime-copy-retry-005/` directory and their SHA-256 values match the integration report: original `83056fb9c9ec0f1de076f24363de8365073c0d9a340724a448634b25188253da`, patched `6bec38a3824a8320dd065829a5c33de49844d8de48ec7b4b2e8908b79473694c`. They are supplemental artifacts, not among run-001 review task's declared `input_sha256` paths.

Both trace sidecars show `max_events=2048`, `attempt_count=683`, `status=event_limit`, exactly 682 arrivals at the retry target after a completed stability boundary, and the final incomplete recorded attempt at `0x0012A85C` with no stability check. Neither records a stable commit. This confirms the event ceiling's partial-capture description; the 682 debugger-observed retry edges under this highly interrupted run do not estimate a natural retry count, elapsed time, or a target retry bound. The pinned helper has no internal retry limit; the event ceiling and RSP timeout are external capture limits. The separate run-002 single-breakpoint capture records stable-branch arrival but does not count its retry iterations.

## Runtime differences, offline gates and integrity

The aggregate run-002 report is `observed`. Both original/patched runs reached the field manager, reached the load-complete checkpoint, and recorded 250 field ticks. The report comparisons for title entry/state 8, save/load callback snapshots, post-confirm progress, and its bounded field-scene signature are equal; `post_confirm_events_equal` is false. This is partial checkpoint evidence, not H4 or whole-game equivalence.

All four offline reports pinned in run-001 passed their scoped gate: H3 entry/IPS report (IPS round-trip true; final image hash `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`, IPS hash `b11128bd8b6510accb502f15423fabc5cf69999b01610ed7aadff31f5d5a7b8e`); H3 caller assertions with negative control detected; H4 direct-reader 119 cases and zero differences with negative control detected; and H4 camera six cases with mutation detected. These offline artifacts do not establish source-producer semantics or physical-input provenance.

Each staged save in the runtime sidecars is 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` before and after; `save_unchanged` and within-run non-mod profile-manifest equality are true. The original and patched starting profile manifests differ in six non-mod files (Qt configuration, two logs, two OpenGL shader caches, and `sysdata/play_time.bin`). This is per-run preservation, not identical profile baselines. The integration report also cites a separate external source-save hash check; I did not access the source save.

The run used controlled GDB writes for the title/save/field checkpoint and logical load confirmation; the copy-call probes themselves are passive reads. No physical/front-end input or axis data was injected. No producer/thread identity, active live input mapping, player movement, interaction, zone transition, or equivalence claim follows.

## Frozen artifact identities and disposition

Run-001 packet hashes matched, including `code.bin` (`1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`), retry report `93a97a696fd324248c1948606e51e03554161696052862d717fd694da7956348`, original sidecar `b62fedceb72cb5ec5cc941a201f73d1ec9e41e9dff09bfcaa2f2e6a6c8f52bcc`, patched sidecar `f860714b7ed603978ad3eef56b3bc09589888ef5cdfab0d636f5bb12d2d96a6f`, and reviewed integration report `b29ac135145c24187e5a30529a44d996b895e50db29dfe0f254aebceec1bbf4e`. Offline report hashes are in the pinned task packet; the auxiliary raw trace hashes are listed above and match the documentation, but are not task-pinned inputs.

Accept the bounded derivation and stable-branch evidence with two scope qualifications: the successful load's `r3`/payload is inferred from `r4` and static code, and the source bytes sampled after the branch may not be the bytes loaded during the successful copy. The destination at the boundary and caller result/output are the evidence of the copied record. Preserve retry-count, save/profile, input-source, and equivalence limits as above. No runtime, build, test, or source-save operation was performed in this review.

Declared companion identities reviewed from the run-001 packet: runner `tools/h3_autonomous_verify.py` SHA-256 `927a16db9be87db17edaf6fc2ce3d755742c2fbff8f83a5ea9c7e195c4db6dc3`; offline H3 entry report `24eb0655613c24554fe87883eeb01d71f8f3f18a2ad131dff47b55104f2f8bd4`; H3 caller report `c261e11f45bcee23f9a886f840b61a4065abcf474700c66971f9d89e3cd96314`; H4 direct report `f0f33937d6fde6774617efd43d51174b623d8eeb33b4510f7a4f4422f68a5cab`; H4 camera report `0fbb05901d7c27feddb401623c13f23225746b6dfe14a3ff224de8d1bc73521b`. All declared run-001 input pins matched when checked.

## Run-002 final text recheck

The updated integration wording now matches the reviewed sidecars and pinned code: `committed_source_payload` is read only after the stability branch reaches `0x0012A8DC`; at that stop the source header `+0x10` reads 5/6 while live `r4` is 1/2, so it cannot be treated as the compared snapshot or evidence that the source remained unchanged. The destination at the commit boundary, then the caller result/output and post-transform output, are the direct evidence for the copied record. The successful load's `r3` was not captured, so the slot/index remains derived from live commit `r4`, first loop index, and pinned ARM arithmetic. This recheck was text-only; no runtime was repeated.
