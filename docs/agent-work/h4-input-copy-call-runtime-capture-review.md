# H4 input-copy runtime capture: independent review

## Result

All declared SHA-256 pins in `build/agent-work/H4-semantic/h4-input-copy-call-runtime-capture-review/run-001/task.json` match. The paired raw sidecars, aggregate report, and pinned ARM code support the core bounded observations: both runs hit all six configured probes; the first observed copy iteration selected source index 3 in the original process and 2 in the patched process; both sampled payloads and destination bytes were zero; the caller later read result count 1; and both post-transform output records were zero.

The first observed iteration was unstable and therefore its source slot must not be presented as the committed slot. There is an additional control-flow inference the integration report should state precisely: at `0x0012A89C`, the captured `r4` values are 3 and 2, while the contemporaneous source `+0x10` snapshots are 5 and 4. The ARM helper compares the reloaded `+0x10` against its saved count and branches back to `0x0012A780` on mismatch. At `0x0011C644`, the caller-local result count is 1. Since the helper clears that output at entry and writes the positive selected count only on its stable-comparison path, the result implies a later stable helper pass returned one record. The trace does **not** identify the later pass's slot or payload: it records only one hit at each breakpoint.

## Address, ABI and timing audit

The pinned `code.bin` hash is `1f98884fe997af22e032a14c51a46c872b05b0e079a0f29e307b0e059cfaa558`. Static disassembly confirms:

- `0x0011C640` is the `BL 0x0012A758`. The call has `r0=0x10000000`, `r1=0x004E3C28`, `r2=1`, and `r3=SP+8`. At that boundary `SP=0x0FFFFEC8`, so the result-count output pointer is `0x0FFFFED0`. The two stack arguments at `[SP]` and `[SP+4]` point to `0x0FFFFED8` (the two-word cursor pair) and `0x0FFFFED4` (the second local word); both pointees were initially `0xFFFFFFFF`.
- The caller's result-count local at `[SP+8]` had stale bytes `0c3a4e00` before the helper zeroed it. It was `00000000` by the payload/stability probes and `01000000` at the caller's post-call boundary. The reported count 1 is correctly read from the local at `[SP+8]`, not treated as a return-register value.
- `0x0012A85C` is the first payload load (`ldr r10,[r3,#0x28]`), and the breakpoint occurs before that instruction executes. Immediately before it, `r2` holds the calculated index, `r3` the calculated source-slot base, `r5` the loop index, and `r7` the destination slot. The captured index/base pairs are `(3,0x10000030)` original and `(2,0x10000020)` patched; both destination slots are `0x004E3C28`. Adding the payload offset `0x28` gives actual memory-read addresses `0x10000058` and `0x10000048`.
- The source/destination reads are range-checked against the runner's broad user-memory bound. The captured source slots and their payload spans also fall inside the validated `[0x10000000,0x10000100)` source span; the report should not imply the runner separately enforces this containment for every selected slot.
- `0x0012A89C` is the beginning of the helper's snapshot-check instructions, before the first `ldr` there. The captured destination-after-copy bytes are thus after the five copy instructions but before the comparison/branch. `0x0011C644` is the caller's first instruction after the helper and is before its count-local load; `0x0011C66C` is after `0x00128610` returned and captures the post-transform record.

### Snapshot timing correction

The report's phrase “the helper entry ... read a source count word of 6” conflates a debugger memory read at the **function-entry breakpoint** with the later helper `ldr`. At `0x0012A758`, execution has not entered the body far enough to execute its source-header loads; the sidecar records that the source memory snapshot at this breakpoint contained `+0x10 = 6` on both sides. The actual helper load is at `0x0012A780`. At the copy breakpoint `0x0012A85C`, the captured general registers show `r4=3` (original) and `r4=2` (patched), and the static positive-count path leaves that value as the loop's `r4`. Meanwhile the source-memory snapshot taken at that breakpoint reads `+0x10 = 6` original and `2` patched. The source header is changing during the call; boundary snapshots should be labeled by capture point, not described as the exact value consumed by the helper's initial load unless `0x0012A780` is itself observed.

At `0x0012A89C`, the memory snapshot reads `+0x10 = 5` original and `4` patched, whereas the captured `r4` remains 3 and 2 respectively. The static next comparison is therefore inconsistent on the observed count field and sends that iteration back to `0x0012A780`. This is a strong static-plus-boundary inference, but the report correctly notes it did not record the branch instruction or the next selected slot. The later count 1 proves completion through a stable pass under the helper's pinned control flow; the pass's source address and payload remain missing.

## Paired raw evidence and interpretation

| Boundary | Original | Patched | Review |
|---|---|---|---|
| `0x0011C640` caller | source `0x10000000`, output `0x004E3C28`, request 1, count pointer `0x0FFFFED0` | same | Arguments, output and stack-local pointers match. Header snapshots themselves differ and are volatile. |
| `0x0012A758` entry snapshot | source header `+0x10=6`; cursor pair initially `FFFFFFFFFFFFFFFF` in caller locals | same count and local pair | This is a pre-body memory snapshot, not proof that `ldr [r0+0x10]` later read 6. |
| `0x0012A85C` first observed payload load | index 3, source slot `0x10000030`, payload at `0x10000058` | index 2, source slot `0x10000020`, payload at `0x10000048` | Both 16-byte sampled payloads and both destination-before-copy records are zero. This is the first observed iteration only. `r4` is 3/2 at this boundary. |
| `0x0012A89C` first observed stability check | memory `+0x10=5`, `r4=3` | memory `+0x10=4`, `r4=2` | Both disagree on count. Destination-after-copy is zero on both. The static helper retries on this mismatch; no later attempt breakpoint is recorded. |
| `0x0011C644` after helper | result local `[SP+8]=1`; cursor pair `b03c98752c000000`; second local `1`; output zero | result local `[SP+8]=1`; cursor pair `5135c5c72c000000`; second local `5`; output zero | The result is sourced from the caller local. The different cursor/local values are raw observations, not identified semantics. Positive result plus the helper's code implies stable completion on a later pass, but not its slot. |
| `0x0011C66C` after transform | output 16 bytes zero | output 16 bytes zero | Post-transform value is separately observed and equal for these bytes. |

All six configured addresses hit in both sidecars. The helper's internal retry is unbounded in the pinned code; the runner's single-breakpoint-per-address pass is not an attempt trace and imposes no bound on the helper. A follow-up should log each `0x0012A780` iteration, the `r4`/snapshot loaded on that iteration, computed index/source address and destination, each check result/branch, and the final stable path at `0x0012A8DC`. It needs an external timeout and should report the final committed slot only after observing that final iteration.

## Read-only probes versus runtime setup writes

The six copy-call probes themselves use GDB breakpoint control and `rsp_read_mem`/register reads; they do not write the sampled source or destination, and this invocation did not request the optional axis-output override. However, the **overall runner session is not guest-write-free**. Its existing checkpoint setup patches/restores the UI input-getter stub, writes title work state to reach the save UI, temporarily installs/restores the logical confirm stub at `0x002BFFBC`, and supplies a logical Load complete getter result by writing `r0`/`PC`. Those are controlled debugger writes used to navigate to the field checkpoint, not physical-input injection and not part of the H4 source/destination probe. The report should say “passive read-only copy-call probes after controlled GDB-driven checkpoint setup,” not “the task did not write guest memory.” The temporary confirm stub restoration is recorded as true in both sidecars.

The runner address-range guards validate each bounded RSP read before it is issued. For this run the source base validation at caller entry is true for 0x100 bytes; all selected payload, destination, header, and stack reads shown in the sidecars have `range_valid: true`. The guard is a broad address-range check, not a lock or protocol guarantee; it does not stop a guest writer from changing a source between separate reads or establish atomic record ownership.

## Offline, runtime and integrity scope

The pinned offline artifacts are consistent with the report and are appropriately prerequisites, not H4 copy-helper proof: H3 entry placement report is `passed` with IPS round-trip true, 495 IPS records, final-image hash `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8` and IPS hash `b11128bd8b6510accb502f15423fabc5cf69999b01610ed7aadff31f5d5a7b8e`; H3 caller composition assertions all pass and its modified-next-state negative control is detected; H4 direct reader report has 119 cases, zero differences and a detected negative control; H4 camera composition has six cases and a mutation control. These reports do not validate the source object's producer or the copy helper's dynamic stable-slot semantics.

`report.json` says `status=observed`, not pass/equivalent. It records equal title-entry registers, load-complete acknowledgments, field-manager reachability, field-scene signatures/tick count and progress, plus false comparisons for title state 8, save/load callbacks and post-confirm events. Each sidecar has 250 field-scene observations (250 ticks; 249 successful next-tick statuses). Treat the equal field signature as the report's bounded signature comparison, not full state equivalence. No H4 equivalence or whole-game equivalence follows.

For each sidecar, the staged profile save before/after is 151,088 bytes with SHA-256 `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9`; `save_unchanged=true` and the within-run non-mod profile manifest is unchanged. The original and patched starting profile manifests are not identical: six non-mod entries differ (Qt config, two Azahar logs, two OpenGL shader caches, and `sysdata/play_time.bin`). Preserve this as within-run integrity, not matching profile baselines. The JSON hashes staged copies; the source-save hash is an external check recorded in the run handoff/integration notes. I did not access the source save.

The earlier preliminary run with a result register captured before `ldr [SP+8]` is explicitly excluded. This review uses corrected `runtime-copycall-002` raw reports and confirms the result local pointer is `SP+8`, matching call-site `r3` at `0x0011C640`.

## Recommendation and limits

Accept the sampled addresses, the zero payload/output values at those boundaries, and the observed original/patched first-attempt index difference as narrow runtime evidence. Revise the two wording points above, and distinguish inferred later stable completion from directly observed retry iteration/slot. Maintain the report's existing restrictions: no producer/thread attribution, physical input, active stick data, player movement, interaction, or H4 semantic equivalence. The concrete next evidence is the bounded per-attempt trace through the retry edge and stable commit, with actual final source address and payload; no new emulator run is part of this review.

## Frozen report identities

These hashes are the packet-pinned input artifacts reviewed here (not new outputs of this review):

- `runtime-copycall-002/report.json`: `d6edc9d1111773fc2f08b242e9e6a2619d2cf71fd7bf4e2c832c88d3801df437`
- `runtime-copycall-002/original.json`: `ad9172060b65fb926b329c8dd4a9184f1eba2d06d52ac6b9f1e26526cf9594e7`
- `runtime-copycall-002/patched.json`: `0bbcaefc7e316def1fdbe8e926ade2f074c8c3bf7e8703b2d6b8712d7f28add5`
- `offline2-h3-entry/report.json`: `aa44e9e3002ea308cdf1b2ffa7f77038180a11946bc7c7409ca8db55bde52c5b`
- `offline2-h3-caller/report.json`: `1ea40ea5228bc4d6b3057b6ec4568dbbaa07b3b620ecb277fa0f748f8251d38c`
- `offline2-h4-direct/report.json`: `f0f33937d6fde6774617efd43d51174b623d8eeb33b4510f7a4f4422f68a5cab`
- `offline2-h4-camera/report.json`: `0fbb05901d7c27feddb401623c13f23225746b6dfe14a3ff224de8d1bc73521b`

All task input hashes, including these artifacts, matched at review. The report paths are dependencies of the capture task, not outputs under this review packet; the review handoff therefore does not list them as newly generated reports.

## Run-002 final recheck

The run-002 packet pins the updated integration report and all reviewed raw/runtime/offline inputs; every declared hash matched. The integration text now accurately distinguishes the pre-body `0x0012A758` memory snapshot (`+0x10=6`) from the later helper load at `0x0012A780` and the live `r4=3/2` at the first copy boundary. It also correctly states that the mismatch at the observed stability check leads back to the retry path and that caller result count 1 plus the pinned success-only store implies a later stable pass, without claiming its slot/payload was observed. Finally, it separates passive copy-call probes from controlled GDB guest writes used to reach the checkpoint and explicitly says no axis or physical/front-end input was injected. These corrections match the frozen evidence. No runtime was rerun and no runner or integration file was edited in this recheck.
