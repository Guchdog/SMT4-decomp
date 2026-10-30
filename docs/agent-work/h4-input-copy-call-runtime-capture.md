# H4 input-copy call runtime capture

## Scope and validation

This is a paired original/H3-patched, no-axis-input observation at the H3 Shinjuku field checkpoint. The copy-call probes capture call arguments and bounded memory with GDB RSP reads only. The runner's setup to reach the field checkpoint uses controlled GDB writes to title state, a temporary logical input-getter stub, and registers; those writes are restored or are part of the controlled checkpoint transition. No axis data or physical/front-end input was injected. Both profiles reached the field manager and completed 250 ticks.

Before the final paired run, the following offline-first checks passed: H3 entry placement/IPS/interworking audit, H3 title-load differential with its negative control, H3 caller composition, H4 direct reader differential (119 cases plus negative control), and H4 camera composition (six cases plus mutation control). The generated H3 final image SHA-256 was `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`; its IPS SHA-256 was `b11128bd8b6510accb502f15423fabc5cf69999b01610ed7aadff31f5d5a7b8e`.

## Observed copy sequence

The final corrected run is `build/agent-work/H4-semantic/h4-input-copy-call-runtime-capture/run-001/checks/runtime-copycall-002/report.json` (`SHA-256 d6edc9d1111773fc2f08b242e9e6a2619d2cf71fd7bf4e2c832c88d3801df437`). All six configured probes hit in both processes: caller BL at `0x0011C640`, helper entry `0x0012A758`, source payload-load boundary `0x0012A85C`, helper snapshot-check boundary `0x0012A89C`, caller after helper `0x0011C644`, and caller after transform `0x0011C66C`.

At `0x0011C640`, both runs passed `r0=0x10000000` (source object), `r1=0x004E3C28` (output), `r2=1`, and `r3=SP+8`; the call frame's two stack pointers addressed local cursor and count words initially set to `0xFFFFFFFF`. The debugger's source-memory snapshot at the helper-entry breakpoint `0x0012A758` showed `+0x10=6` in both runs. This breakpoint is before the helper body loads that field at `0x0012A780`, so 6 is not established as the value consumed by the helper. At the first observed payload-load boundary `0x0012A85C`, the live `r4` values were 3 (original) and 2 (patched), while source-memory snapshots showed `+0x10=6` and 2 respectively. The loop index was 0; selected source-slot indices were 3 in original (`r3=0x10000030`) and 2 in patched (`r3=0x10000020`); `r7=0x004E3C28` was the destination in both. The selected 16-byte payload at source slot `+0x28` and destination bytes before the copy were all zero.

At `0x0012A89C`, source-memory snapshots showed `+0x10=5` original and 4 patched, while the captured `r4` remained 3 and 2. The helper's comparison therefore sends these sampled iterations back to `0x0012A780`; the trace did not record the branch itself or another iteration. At `0x0011C644`, the corrected read of caller local `[SP+8]` showed result count 1 on both sides. The pinned helper clears this local at entry and writes a positive count only on its stable-comparison path. Thus the result implies a later stable pass returned one record, although this trace does not reveal that pass's selected slot or payload. The raw 16-byte output after helper return and the separate 16-byte output after `0x00128610` were zero on both sides.

The caller-local cursor/count outputs differed between processes: the cursor pair after return was `b03c98752c000000` in original and `5135c5c72c000000` in patched; the second local word was 1 and 5 respectively. The result-count local was 1 on both sides. The object span and primary/alternate input records remain process-specific evidence; no type or physical-input mapping is inferred from these values.

## Comparison and integrity

The aggregate paired report is `observed`: title-entry registers matched, but `title_state8_equal`, `save_load_callbacks_equal`, and `post_confirm_events_equal` were false in this run. Both runs nevertheless reached the field manager, had equal reported field-scene semantics/progress and tick observations, and their staged save/profile manifests remained unchanged within each run. This is partial checkpoint evidence, not equivalence for the full load path or game.

The user source save's known pre-run digest and separate direct post-run hash were `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` (151,088 bytes). Each staged profile save retained that digest before and after. The original and patched starting profile manifests differ in six non-mod files; within-run manifest preservation is not an identical-profile-baseline claim. Azahar processes terminated after the runner.

## Limits and next observation

The first source-slot address and payload were captured, but the helper's first observed consistency attempt was unstable. The result count plus pinned control flow implies a later stable pass, but its source address and payload are unknown. The target helper has an unbounded internal snapshot-retry loop. A future observation needs to capture each attempt through either the retry edge at `0x0012A780` or stable commit at `0x0012A8DC`, with a separate external timeout. It must not assign the first observed slot to the final output without evidence. No producer/thread, physical input, player movement, interaction, or H4 equivalence is established.

An earlier preliminary run captured the result register before its `ldr` and was excluded; this final report uses the corrected local-word read at `[SP+8]`.
