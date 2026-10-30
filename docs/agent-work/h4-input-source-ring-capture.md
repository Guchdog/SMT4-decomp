# H4 input source object runtime capture

## Scope

This is a paired, read-only observation of the H3 title-load reconstruction and the pinned original at the H4 field checkpoint. The runner captures a bounded 0x100-byte memory span at the observed source address in the `0x0011C640` producer probe, retains the entry registers and stack bytes, and rereads the same validated address after the bounded producer-probe sequence. The added reads use the GDB RSP memory-read command; this capture path does not write guest memory or registers.

The run used the controlled logical load-confirm path (`trigger_id=0`, slot 0) to reach the field scene. It did not inject axis data, use physical/front-end input, or claim player movement. Each side reached the field manager and completed 250 field ticks.

## Runtime evidence

The paired run is `build/agent-work/H4-semantic/h4-input-source-ring-capture/run-003/checks/runtime-source-ring-004/report.json` (`SHA-256 1c67789bae77552962b99a025a2b32bfa8d89855d5b8fd0c998afbf0ec6d23645`). Both original and patched runs reached the field manager and produced equal reported field-scene semantics and tick counts. The aggregate report also records equal title-entry registers, title state-8 bytes, save/load callback signatures, and post-confirm progress. Some post-confirm event details differ; this is not treated as a whole-game equivalence result.

At probe `0x0011C640`, both runs had `r0=0x10000000`, `r1=0x004E3C28`, and `r2=1`. The candidate span `[0x10000000, 0x10000100)` passed the runner's address-range check. The captured stack cursor was `sp=0x0FFFFEC8`, with `r3=0x0FFFFED0`, `lr=0x0011C620`; the full entry GPR and 0x40-byte stack snapshots remain in the raw report. Probe `0x0011C644` separately records its entry register and stack values. Static code at `0x0012A758`, the target of this call, reads source-object offsets `+0` and `+8` as two 64-bit snapshot values and `+0x10` as a count; its snapshot comparisons and arithmetic treat the first two values as cursors. This static shape does not identify their higher-level meaning.

The source bytes changed between entry and the reread after the four-probe sequence on both sides. In each 0x100-byte span, changes were limited to offsets `0x00–0x03`, `0x08–0x0B`, `0x10`, `0xA8–0xAB`, `0xB0–0xB3`, and `0xB8`. The dword at `+0x10` changed from 3 to 6 in the original and from 0 to 4 in the patched run; the same pattern appears at `+0xB8`. The 64-bit snapshot values at `+0` and `+8` changed. Bytes at `+0xA8` and `+0xB0` changed in the same way within each capture, but the inspected call does not establish their relationship to the `+0`/`+8` fields. The counter values and bytes are observations only; object ownership, update cadence, and higher-level meaning remain unresolved.

Before and after the capture, the primary input record span at `0x004E3C28` (0x30 bytes), alternate record at `0x004E3C48` (0x10 bytes), counter span at `0x004E3C58` (0x7C bytes), and calibration record remained identical within each run. The input records and counters observed at the probes were zero. This bounded result does not establish whether physical input was available to Azahar, which input API feeds the source object, or whether a captured count represents live input.

## Integrity and validation

- The user-provided source save `E:\emulador3ds\sdds4game1.sav` had the known pre-run SHA-256 and a separately checked post-run SHA-256 of `6d8d15c90a270e993c057f906e0714a62f9c6260b04713f2a789c475e69d22e9` (151,088 bytes). Both staged profile saves had this hash before and after the paired run. Each profile's non-mod manifest stayed unchanged within that run, and the Azahar processes terminated at the end of the runner. The original and patched starting manifests were not identical: six non-mod entries differed (Qt configuration, two logs, two OpenGL shader caches, and `sysdata/play_time.bin`). The integrity result is within-run preservation, not identical profile baselines.
- Offline-first checks passed before this runtime run: H3 entry placement/IPS/interworking audit (`offline-h3-entry`), H3 title-load differential with negative control, H3 caller composition (`offline-h3-caller`), H4 direct reader differential (119 cases plus detected negative control), and H4 camera composition (six cases plus detected mutation).
- The H3 composed-image hash for the run was `af2bc749364703ac11d1b663527a1ea339c571e14f89e0aa4e919c58f71436d8`; its generated IPS hash was `b11128bd8b6510accb502f15423fabc5cf69999b01610ed7aadff31f5d5a7b8e`.
- A preliminary attempt with newly cloned C-drive profiles stopped before slot confirmation because the emulator presented an empty slot. It is excluded from this evidence. The successful run used the already validated, isolated `h3-runtime-isolated-run-042` original/patched pair, whose save/profile integrity was checked before and after.

## Limits and next work

This is source-object and caller-state evidence, not a recovered C++ contract. It does not prove that `0x10000000` is a ring buffer, that its changing dwords are event counts, or that it contains joystick samples. Next, statically trace writers and consumers of the snapshot values at `+0`/`+8`, count at `+0x10`, and the changed fields at `+0xA8`/`+0xB0`; choose a safe, bounded synthetic fixture only if that contract can be established. Preserve the raw paired report and its limitations in any later claim.
